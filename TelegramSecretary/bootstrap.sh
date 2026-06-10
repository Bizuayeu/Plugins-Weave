#!/bin/bash
# TelegramSecretary bootstrap — idempotent setup for cloud routine / manual runs.
#
# Use:
#   source <INSTALL_DIR>/bootstrap.sh
#     → exports TELEGRAM_SECRETARY_SESSION_ID into the parent shell so subsequent
#       lease/watch/send-reply commands share the same owner (運用律 B 案)
#   bash   <INSTALL_DIR>/bootstrap.sh
#     → installs only, env exports do not persist
#
# Single source of truth for runtime deps: <INSTALL_DIR>/pyproject.toml
# source/exec デュアル対応の bootstrap パターン.

set -u

# Detect source vs exec so we can use `return` when sourced, `exit` when executed.
_ts_sourced=0
if [ "${BASH_SOURCE[0]:-}" != "${0:-}" ]; then
    _ts_sourced=1
fi

_ts_die() {
    echo "[telegram-secretary-bootstrap] FAIL: $*" >&2
    if [ "$_ts_sourced" = "1" ]; then
        return 1
    else
        exit 1
    fi
}

_ts_log() { echo "[telegram-secretary-bootstrap] $*"; }

# 物理パス化（symlink/junction 成分を解消）。存在しないパスも python の realpath が
# 解決できる範囲で正規化する（cd && pwd -P は不在パスで使えない）。
_ts_phys_path() { python -c 'import os, sys; print(os.path.realpath(sys.argv[1]))' "$1"; }

# registry worktree 再provision前のサニティチェック。
# config の registry_dir 誤設定（既存の実データディレクトリ等）を黙って rm -rf しないため、
# 「不在 / 空 / registry 既知エントリのみ」のときだけ破壊的再provisionを許す。
# 既知エントリ = worktree の .git、registry 4 表 + wal の各ディレクトリ、空ブランチ用 .keep。
# 未知エントリが 1 つでもあれば 1（呼び出し側が warn+skip、graceful 方針は worktree add 失敗時と同じ）。
_ts_reg_safe_to_wipe() {
    [ ! -e "$1" ] && return 0   # 不在: rm -rf は no-op、worktree add が新規作成する
    [ ! -d "$1" ] && return 1   # ディレクトリ以外（ファイル/リンク）: 触らない
    local _entry _base
    for _entry in "$1"/* "$1"/.*; do
        _base="${_entry##*/}"
        case "$_base" in .|..) continue ;; esac
        [ -e "$_entry" ] || continue   # glob 不一致の literal はスキップ
        case "$_base" in
            .git|.keep|individuals|tasks|knowledge|abilities|wal) continue ;;
            *) return 1 ;;
        esac
    done
    return 0
}

# Resolve script dir robustly whether sourced or executed.
_ts_script_path="${BASH_SOURCE[0]:-$0}"
_ts_script_dir="$(cd "$(dirname "$_ts_script_path")" && pwd)"

# --- 依存導入（pyproject.toml が SSoT、Tier 別に cloud routine 起動コストを制御）---
# editable install（packages=[] なので依存導入専用）で pyproject の extras を引く。
# ピンを bootstrap に再記述しない（二重管理だと片側だけ更新されるドリフトの温床）。
# base: httpx のみ。Heavy モード時に media extras（markitdown/pdf 系）、さらに voice extras を追加。
# media を扱わない Medium 運用・keep-alive 検証は base だけで起動が軽い（FINDING A/B）。
# voice(moonshine+av) は BUNDLE_VOICE=false で除外可（moonshine Community License は年商$1M未満のみ
# 商用無料・~134MB model ゆえ大規模/ライセンス回避向け）。未導入時は watch が transcriber=None で
# 起動し音声を skipped にフォールバック（FINDING B、render usecase は transcriber Optional）。
if [ "${TELEGRAM_SECRETARY_MEDIA_ENABLE_DOWNLOAD:-true}" != "false" ]; then
    if [ "${TELEGRAM_SECRETARY_BUNDLE_VOICE:-true}" != "false" ]; then
        _ts_log "Heavy mode: installing media+voice extras from pyproject..."
        python -m pip install --quiet -e "$_ts_script_dir[media,voice]" || _ts_die "media+voice deps install failed"
    else
        _ts_log "Heavy mode (BUNDLE_VOICE=false): installing media extras from pyproject..."
        python -m pip install --quiet -e "$_ts_script_dir[media]" || _ts_die "media deps install failed"
        _ts_log "voice deps skipped (BUNDLE_VOICE=false) -> 音声は skipped にフォールバック"
    fi
else
    _ts_log "Medium mode (MEDIA_ENABLE_DOWNLOAD=false): installing base deps only (httpx)..."
    python -m pip install --quiet -e "$_ts_script_dir" || _ts_die "base deps install failed"
fi
python -c "import httpx" >/dev/null || _ts_die "httpx import failed after install"

# --- Session ID 自動 export (運用律 B 案) ---
# lease acquire / watch / send-reply / lease renew が同じ owner を共有するように、
# bootstrap で session_id を session 全体に固定する。既に設定されていれば尊重 (冪等)。
export TELEGRAM_SECRETARY_SESSION_ID="${TELEGRAM_SECRETARY_SESSION_ID:-session-$(python -c 'import uuid; print(uuid.uuid4().hex[:8])')}"
_ts_log "session_id=$TELEGRAM_SECRETARY_SESSION_ID"

# --- INSTALL_DIR と STATE_DIR の絶対パス固定 (subshell cd でズレないように)---
# 後続 Step は (cd "$TELEGRAM_SECRETARY_INSTALL_DIR" && ...) で subshell cd する。相対 STATE_DIR は
# その subshell cwd 基準で解決され幽霊パス化するため、bootstrap 実行時に skill root (INSTALL_DIR) 基準で
# 絶対化して固定する。既定 ./state は <INSTALL_DIR>/state/ に解決され、
# .gitignore の `/state/` に引き続きマッチする。
# INSTALL_DIR（=skill root, _ts_script_dir）を自己解決して export。ROUTINE_PROMPT の各 bash call が
# config.json / scripts へ到達する唯一の基点。skill が repo 内のどこに置かれても、また junction 経由でも
# 自分の物理位置から絶対解決するため、別途 repo root の階層計算（旧 ../..）は不要（配置非依存）。
export TELEGRAM_SECRETARY_INSTALL_DIR="$_ts_script_dir"
export TELEGRAM_SECRETARY_STATE_DIR="$(python -c 'import os, sys; print(os.path.abspath(os.environ.get("TELEGRAM_SECRETARY_STATE_DIR") or sys.argv[1]))' "$_ts_script_dir/state")"
_ts_log "install_dir=$TELEGRAM_SECRETARY_INSTALL_DIR state_dir=$TELEGRAM_SECRETARY_STATE_DIR"

# --- 設定検証 (env + config.json の欠損/不正は exit 2 で fail-fast) ---
# validate-config を deadline 計算より先に実行する。config.json 不在/欠落/範囲外をここで弾けば、
# 後段の session_duration_sec 取得は「検証済み」前提で単純化できる（取得前に die させる）。
(cd "$_ts_script_dir" && python scripts/main.py validate-config) || _ts_die "validate-config failed"

# --- REGISTRY_DIR の絶対パス固定 (registry_dir も cwd 依存 .resolve() を回避)---
# config.json の registry_dir（2リポ親起点の相対）を bootstrap 実行時 cwd（=2リポ親）基準で絶対化して
# env 注入する。registry コマンドは後続 call で (cd "$TELEGRAM_SECRETARY_INSTALL_DIR" && ...) するため、
# config.py 側の .resolve()（cwd=skill root）では二重ネストの幽霊パス化する（state_dir と同型）。
# config.json が値の正典、env は解決済み絶対パスのキャリア（STATE_DIR と同型）。未設定なら注入せず
# config.py が state_dir フォールバック。bootstrap source 時の cwd は 2リポ親（ROUTINE_PROMPT Step 2、cd 前）。
_ts_registry_raw="$(python -c 'import json, sys; d = json.load(open(sys.argv[1], encoding="utf-8")); print(d.get("registry_dir") or "")' "$_ts_script_dir/config.json")"
if [ -n "$_ts_registry_raw" ]; then
    export TELEGRAM_SECRETARY_REGISTRY_DIR="$(python -c 'import os, sys; print(os.path.abspath(sys.argv[1]))' "$_ts_registry_raw")"
    _ts_log "registry_dir=$TELEGRAM_SECRETARY_REGISTRY_DIR"

    # --- REGISTRY worktree provisioning（層1 根治：registry_dir を独立 git 作業ツリー化）---
    # registry_sync 有効時、registry_dir を Private リポの第二作業ツリー（worktree）として冪等に用意する。
    # これで GitCliAdapter の cwd=registry_dir が独立作業ツリーになり、起動時 fetch_checkout の
    # checkout -B が親 Private dev ツリーを汚染せず（欠陥2）、registry_dir 不在の OSError(Errno 2)
    # （欠陥1）も解消する。ts-registry は registry ファイルを root 直下に持つ専用ブランチ。
    # provisioning 失敗時は _ts_die せず継続し、registry-sync が空ロード警告（層3）を出す
    # （fail-fast でなく graceful。worktree add の dev ツリー非干渉は技術検証で実証済み）。
    # worktree add は -B "$BR" ... "origin/$BR" で常に origin から強制（registry の SSoT は origin）。
    # stateful 環境（手動/ローカル実行）に古い同名ローカルブランチが残っても掴まず最新を反映し、
    # 既存 worktree のリフレッシュ（checkout -B "origin/$BR"）と origin 強制で対称。
    _ts_reg_sync="$(python -c 'import json,sys; print(str(json.load(open(sys.argv[1],encoding="utf-8")).get("registry_sync", False)).lower())' "$_ts_script_dir/config.json")"
    if [ "$_ts_reg_sync" = "true" ]; then
        _ts_reg_branch="$(python -c 'import json,sys; print(json.load(open(sys.argv[1],encoding="utf-8")).get("registry_branch") or "claude/ts-registry")' "$_ts_script_dir/config.json")"
        # Private リポルート = private_dir の先頭パスセグメント（cwd=2リポ親起点）
        _ts_priv_repo="$(python -c 'import json,sys; p=(json.load(open(sys.argv[1],encoding="utf-8")).get("private_dir") or "").replace(chr(92),"/").strip("/"); print(p.split("/")[0] if p else "")' "$_ts_script_dir/config.json")"
        if [ -n "$_ts_priv_repo" ] && { [ -d "$_ts_priv_repo/.git" ] || [ -f "$_ts_priv_repo/.git" ]; }; then
            git -C "$_ts_priv_repo" fetch origin "$_ts_reg_branch" 2>/dev/null \
                || _ts_log "warn: registry fetch failed (registry-sync will retry / surface empty-load)"
            # toplevel 比較は物理パス同士で行う（symlink/junction 成分による
            # 「正しい worktree なのに不一致→誤って破壊的再provision」を防ぐ）。
            _ts_reg_top="$(git -C "$TELEGRAM_SECRETARY_REGISTRY_DIR" rev-parse --show-toplevel 2>/dev/null || true)"
            if [ -n "$_ts_reg_top" ] \
                && [ "$(_ts_phys_path "$_ts_reg_top")" = "$(_ts_phys_path "$TELEGRAM_SECRETARY_REGISTRY_DIR")" ]; then
                git -C "$TELEGRAM_SECRETARY_REGISTRY_DIR" checkout -B "$_ts_reg_branch" "origin/$_ts_reg_branch" 2>/dev/null \
                    && _ts_log "registry worktree refreshed ($_ts_reg_branch)" \
                    || _ts_log "warn: registry worktree refresh failed"
            elif _ts_reg_safe_to_wipe "$TELEGRAM_SECRETARY_REGISTRY_DIR"; then
                git -C "$_ts_priv_repo" worktree prune 2>/dev/null
                rm -rf "$TELEGRAM_SECRETARY_REGISTRY_DIR" 2>/dev/null
                git -C "$_ts_priv_repo" worktree add -B "$_ts_reg_branch" "$TELEGRAM_SECRETARY_REGISTRY_DIR" "origin/$_ts_reg_branch" 2>/dev/null \
                    && _ts_log "registry worktree provisioned ($_ts_reg_branch -> $TELEGRAM_SECRETARY_REGISTRY_DIR)" \
                    || _ts_log "warn: registry worktree add failed (registry-sync will surface empty-load)"
            else
                # registry_dir 誤設定の疑い（未知の実データが居る）: 黙って消さない。
                _ts_log "warn: registry_dir has unexpected content; skipping destructive re-provision ($TELEGRAM_SECRETARY_REGISTRY_DIR)"
            fi
        else
            _ts_log "warn: Private repo root not found ($_ts_priv_repo); registry provisioning skipped"
        fi
    fi
fi

# --- deadline 駆動ロングポーリング運用変数 (config.json 化) ---
# 「枠 (deadline)」と「ポーリング回数 (メッセージ頻度で可変)」を分離する。停止主軸は
# TELEGRAM_SECRETARY_SESSION_DEADLINE_EPOCH (時刻)。回数は数えない (早期 exit→返信→再起動)。
# session_duration_sec は config.json が正典 (validate-config 検証済み)。bootstrap はローカル取得して
# deadline を計算するのみ。TELEGRAM_SECRETARY_SESSION_DURATION_SEC env は作らない (純2層: duration 設定値を env に置かない、
# env は秘匿のみ)。deadline_epoch は計算"結果"ゆえ env スナップショットに残してよい。
_ts_duration="$(python -c 'import json, sys; print(json.load(open(sys.argv[1], encoding="utf-8"))["session_duration_sec"])' "$_ts_script_dir/config.json")" || _ts_die "failed to read session_duration_sec from config.json"
export TELEGRAM_SECRETARY_SESSION_DEADLINE_EPOCH="${TELEGRAM_SECRETARY_SESSION_DEADLINE_EPOCH:-$(( $(date +%s) + _ts_duration ))}"  # 停止主軸: この epoch 秒を過ぎたら /goal 停止
export TELEGRAM_SECRETARY_POLL_SET_SEC="${TELEGRAM_SECRETARY_POLL_SET_SEC:-580}"                     # メッセージ無し時の 1 窓上限 (bash timeout より短く)
export TELEGRAM_SECRETARY_POLL_BASH_TIMEOUT_MS="${TELEGRAM_SECRETARY_POLL_BASH_TIMEOUT_MS:-600000}"  # ポーリング call の bash tool timeout (=BASH_MAX_TIMEOUT_MS)
# TELEGRAM_SECRETARY_MAX_TURNS: 日次総量レートキャップ (旧: deadline 異常時の暴走保険、役割変更)。
# 「~15通/h」を最低保証する天井 = アイドル下限(duration/POLL_SET_SEC) + 通数枠(15通/h)。
# 24h→約507 (148+359)、4h→約84 (24+60)。高密度日は最大このturn数まで伸び、到達で当日沈黙
# (lease release→次 cron が offset 継続)。先食い可ゆえ毎時平準化ではない。
# 短 duration (テスト用、約1.4h 未満) では整数除算で算出が過小/0 になり /goal が即死するため
# floor=30 を敷く (0 ターン停止の回避＝最低限の暴走保険予算)。env で上書き可。
_ts_msg_per_hour=15
_ts_max_turns_calc=$(( _ts_duration / TELEGRAM_SECRETARY_POLL_SET_SEC + _ts_msg_per_hour * _ts_duration / 3600 ))
export TELEGRAM_SECRETARY_MAX_TURNS="${TELEGRAM_SECRETARY_MAX_TURNS:-$(( _ts_max_turns_calc < 30 ? 30 : _ts_max_turns_calc ))}"
_ts_log "deadline-driven poll: deadline=$TELEGRAM_SECRETARY_SESSION_DEADLINE_EPOCH (now+${_ts_duration}s from config.json), window<=${TELEGRAM_SECRETARY_POLL_SET_SEC}s, max_turns=${TELEGRAM_SECRETARY_MAX_TURNS}, bash timeout ${TELEGRAM_SECRETARY_POLL_BASH_TIMEOUT_MS}ms"

# --- 派生 env を source 可能ファイルへ書き出し (Bash tool は call 間で env 揮発) ---
# Claude Code / cloud routine の Bash tool は call 毎に fresh shell (cwd のみ persist、env は揮発)。
# 運用律 B 案の「source で親シェルへ引き継ぐ」は成立しないため、後続 Step が各 call 冒頭で
# re-source する env snapshot を残す。TELEGRAM_BOT_TOKEN / AUTHORIZED_CHATS は Environment 注入で
# 各 call に入る & 秘匿のため、ここには書かない (出力漏洩スキャン規律)。
_ts_env_file="${TELEGRAM_SECRETARY_ENV_FILE:-/tmp/telegram-secretary.env.sh}"
{
    echo "# Generated by bootstrap.sh. Re-source at the top of each subsequent Bash call."
    echo "export TELEGRAM_SECRETARY_SESSION_ID=$(printf '%q' "$TELEGRAM_SECRETARY_SESSION_ID")"
    echo "export TELEGRAM_SECRETARY_INSTALL_DIR=$(printf '%q' "$TELEGRAM_SECRETARY_INSTALL_DIR")"
    echo "export TELEGRAM_SECRETARY_STATE_DIR=$(printf '%q' "$TELEGRAM_SECRETARY_STATE_DIR")"
    echo "export TELEGRAM_SECRETARY_SESSION_DEADLINE_EPOCH=$(printf '%q' "$TELEGRAM_SECRETARY_SESSION_DEADLINE_EPOCH")"
    echo "export TELEGRAM_SECRETARY_POLL_SET_SEC=$(printf '%q' "$TELEGRAM_SECRETARY_POLL_SET_SEC")"
    echo "export TELEGRAM_SECRETARY_POLL_BASH_TIMEOUT_MS=$(printf '%q' "$TELEGRAM_SECRETARY_POLL_BASH_TIMEOUT_MS")"
    echo "export TELEGRAM_SECRETARY_MAX_TURNS=$(printf '%q' "$TELEGRAM_SECRETARY_MAX_TURNS")"
    # registry_dir は registry を使う環境でのみ存在（config.json に registry_dir があれば上で絶対化済み）。
    if [ -n "${TELEGRAM_SECRETARY_REGISTRY_DIR:-}" ]; then
        echo "export TELEGRAM_SECRETARY_REGISTRY_DIR=$(printf '%q' "$TELEGRAM_SECRETARY_REGISTRY_DIR")"
    fi
} > "$_ts_env_file" || _ts_die "failed to write env snapshot: $_ts_env_file"
export TELEGRAM_SECRETARY_ENV_FILE="$_ts_env_file"
_ts_log "env snapshot -> $_ts_env_file"

_ts_log "ready"
