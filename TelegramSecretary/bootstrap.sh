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

# Resolve script dir robustly whether sourced or executed.
_ts_script_path="${BASH_SOURCE[0]:-$0}"
_ts_script_dir="$(cd "$(dirname "$_ts_script_path")" && pwd)"

# --- 依存導入（pyproject.toml dependencies が SSoT、Tier 別に cloud routine 起動コストを制御）---
# base: httpx（必須）。Heavy モード時のみ markitdown(docx render) と voice(moonshine+av) を追加。
# media を扱わない Medium 運用・keep-alive 検証は httpx だけで起動が軽い（FINDING A/B）。
python -m pip install --quiet "httpx>=0.27" || _ts_die "httpx install failed"
if [ "${TELEGRAM_SECRETARY_MEDIA_ENABLE_DOWNLOAD:-true}" != "false" ]; then
    _ts_log "Heavy mode: installing markitdown (docx/pptx/xlsx render)..."
    python -m pip install --quiet "markitdown[docx,pptx,xlsx]>=0.1.6" || _ts_die "markitdown install failed"
    # Stage 10: PDF テキスト層抽出（pdfplumber、MIT、pure-python）。passthrough(Read tool 依存)からの移行。
    # Stage 11: 画像 PDF を pypdfium2 で全ページ画像化し to_pil() で png 保存（Pillow）。pdfplumber が
    # 両者を transitive に引くが、pdf_renderer が pypdfium2 を直接 import するため再現性重視で明示 install。
    _ts_log "installing pdfplumber + pypdfium2 + Pillow (PDF text-layer & image render)..."
    python -m pip install --quiet "pdfplumber>=0.11" "pypdfium2>=4.18.0" "Pillow>=9.1" || _ts_die "pdf deps install failed"
    # voice(moonshine+av) は BUNDLE_VOICE=false で除外可（moonshine Community License は年商$1M未満のみ
    # 商用無料・~134MB model ゆえ大規模/ライセンス回避向け）。未導入時は watch が transcriber=None で
    # 起動し音声を skipped にフォールバック（FINDING B、render usecase は transcriber Optional）。
    if [ "${TELEGRAM_SECRETARY_BUNDLE_VOICE:-true}" != "false" ]; then
        _ts_log "installing voice deps (moonshine + av; BUNDLE_VOICE!=false)..."
        python -m pip install --quiet "moonshine-voice>=0.0.59" "av>=17.0" || _ts_die "voice deps install failed"
    else
        _ts_log "voice deps skipped (BUNDLE_VOICE=false) -> 音声は skipped にフォールバック"
    fi
else
    _ts_log "Medium mode (MEDIA_ENABLE_DOWNLOAD=false): media deps skipped, httpx only"
fi
python -c "import httpx" >/dev/null || _ts_die "httpx import failed after install"

# --- Session ID 自動 export (運用律 B 案) ---
# lease acquire / watch / send-reply / lease renew が同じ owner を共有するように、
# bootstrap で session_id を session 全体に固定する。既に設定されていれば尊重 (冪等)。
export TELEGRAM_SECRETARY_SESSION_ID="${TELEGRAM_SECRETARY_SESSION_ID:-session-$(python -c 'import uuid; print(uuid.uuid4().hex[:8])')}"
_ts_log "session_id=$TELEGRAM_SECRETARY_SESSION_ID"

# --- INSTALL_DIR と STATE_DIR の絶対パス固定 (FINDING 3: subshell cd でズレないように) ---
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

# --- REGISTRY_DIR の絶対パス固定 (FINDING 3 同型: registry_dir も cwd 依存 .resolve() を回避) ---
# config.json の registry_dir（2リポ親起点の相対）を bootstrap 実行時 cwd（=2リポ親）基準で絶対化して
# env 注入する。registry コマンドは後続 call で (cd "$TELEGRAM_SECRETARY_INSTALL_DIR" && ...) するため、
# config.py 側の .resolve()（cwd=skill root）では二重ネストの幽霊パス化する（state_dir の FINDING 3 同型）。
# config.json が値の正典、env は解決済み絶対パスのキャリア（STATE_DIR と同型）。未設定なら注入せず
# config.py が state_dir フォールバック。bootstrap source 時の cwd は 2リポ親（ROUTINE_PROMPT Step 2、cd 前）。
_ts_registry_raw="$(python -c 'import json, sys; d = json.load(open(sys.argv[1], encoding="utf-8")); print(d.get("registry_dir") or "")' "$_ts_script_dir/config.json")"
if [ -n "$_ts_registry_raw" ]; then
    export TELEGRAM_SECRETARY_REGISTRY_DIR="$(python -c 'import os, sys; print(os.path.abspath(sys.argv[1]))' "$_ts_registry_raw")"
    _ts_log "registry_dir=$TELEGRAM_SECRETARY_REGISTRY_DIR"
fi

# --- D: deadline 駆動ロングポーリング運用変数 (Stage 10.3 / D 改修、config.json 化) ---
# 「枠 (deadline)」と「ポーリング回数 (メッセージ頻度で可変)」を分離する。停止主軸は
# TS_SESSION_DEADLINE_EPOCH (時刻)。回数は数えない (早期 exit→返信→再起動)。
# session_duration_sec は config.json が正典 (validate-config 検証済み)。bootstrap はローカル取得して
# deadline を計算するのみ。TS_SESSION_DURATION_SEC env は作らない (純2層: duration 設定値を env に置かない、
# env は秘匿のみ)。deadline_epoch は計算"結果"ゆえ env スナップショットに残してよい。
_ts_duration="$(python -c 'import json, sys; print(json.load(open(sys.argv[1], encoding="utf-8"))["session_duration_sec"])' "$_ts_script_dir/config.json")" || _ts_die "failed to read session_duration_sec from config.json"
export TS_SESSION_DEADLINE_EPOCH="${TS_SESSION_DEADLINE_EPOCH:-$(( $(date +%s) + _ts_duration ))}"  # 停止主軸: この epoch 秒を過ぎたら /goal 停止
export TS_POLL_SET_SEC="${TS_POLL_SET_SEC:-580}"                     # メッセージ無し時の 1 窓上限 (bash timeout より短く)
export TS_POLL_BASH_TIMEOUT_MS="${TS_POLL_BASH_TIMEOUT_MS:-600000}"  # ポーリング call の bash tool timeout (=BASH_MAX_TIMEOUT_MS)
# TS_MAX_TURNS: 日次総量レートキャップ (旧: deadline 異常時の暴走保険、役割変更)。
# 「~15通/h」を最低保証する天井 = アイドル下限(duration/POLL_SET_SEC) + 通数枠(15通/h)。
# 24h→約507 (148+359)、2h→約42 (12+30)。高密度日は最大このturn数まで伸び、到達で当日沈黙
# (lease release→次 cron が offset 継続)。先食い可ゆえ毎時平準化ではない。
# 短 duration (テスト用、約1.4h 未満) では整数除算で算出が過小/0 になり /goal が即死するため
# floor=30 を敷く (0 ターン停止の回避＝最低限の暴走保険予算)。env で上書き可。
_ts_msg_per_hour=15
_ts_max_turns_calc=$(( _ts_duration / TS_POLL_SET_SEC + _ts_msg_per_hour * _ts_duration / 3600 ))
export TS_MAX_TURNS="${TS_MAX_TURNS:-$(( _ts_max_turns_calc < 30 ? 30 : _ts_max_turns_calc ))}"
_ts_log "deadline-driven poll: deadline=$TS_SESSION_DEADLINE_EPOCH (now+${_ts_duration}s from config.json), window<=${TS_POLL_SET_SEC}s, max_turns=${TS_MAX_TURNS}, bash timeout ${TS_POLL_BASH_TIMEOUT_MS}ms"

# --- 派生 env を source 可能ファイルへ書き出し (FINDING 1: Bash tool は call 間で env 揮発) ---
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
    echo "export TS_SESSION_DEADLINE_EPOCH=$(printf '%q' "$TS_SESSION_DEADLINE_EPOCH")"
    echo "export TS_POLL_SET_SEC=$(printf '%q' "$TS_POLL_SET_SEC")"
    echo "export TS_POLL_BASH_TIMEOUT_MS=$(printf '%q' "$TS_POLL_BASH_TIMEOUT_MS")"
    echo "export TS_MAX_TURNS=$(printf '%q' "$TS_MAX_TURNS")"
    # registry_dir は registry を使う環境でのみ存在（config.json に registry_dir があれば上で絶対化済み）。
    if [ -n "${TELEGRAM_SECRETARY_REGISTRY_DIR:-}" ]; then
        echo "export TELEGRAM_SECRETARY_REGISTRY_DIR=$(printf '%q' "$TELEGRAM_SECRETARY_REGISTRY_DIR")"
    fi
} > "$_ts_env_file" || _ts_die "failed to write env snapshot: $_ts_env_file"
export TELEGRAM_SECRETARY_ENV_FILE="$_ts_env_file"
_ts_log "env snapshot -> $_ts_env_file"

_ts_log "ready"
