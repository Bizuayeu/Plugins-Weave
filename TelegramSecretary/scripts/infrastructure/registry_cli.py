"""管理表（INDIVIDUALS / TASKS / KNOWLEDGE）CRUD の CLI ハンドラ。

main.py の subcommand から呼ばれる。値オブジェクトで入力を検証してから永続化する
（決定論的 I/O。何を登録/更新するかの判断は エージェント = 重要度の世界）。

`REGISTRY_SPEC` / `read_json_arg` / `registry_service` は wal_cli と共有する公開名
（旧 private 名の越境 import を解消）。git/sync の DI 組み立ては composition.py に移設済み。
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, NamedTuple

from adapters.registry.json_registry_store import JsonRegistryStore
from domain.exceptions import GitSyncError
from domain.registry import (
    Ability,
    Goal,
    Individual,
    Knowledge,
    Profile,
    Step,
    Subject,
    Task,
    derive_role,
    invalid_subjects,
    unknown_keys,
)
from infrastructure.composition import build_git, build_sync
from infrastructure.config import Config
from infrastructure.exit_codes import EXIT_CONFIG_INVALID, EXIT_FETCH_FAILED, EXIT_OK
from usecases.manage_registry import RegistryService
from usecases.orientation import (
    DEFAULT_HANDOFF_CAP,
    DEFAULT_HANDOFF_LATEST,
    DEFAULT_NOTES_TAIL,
    DEFAULT_TOPIC_WIDTH,
    OrientationService,
)

# list 出力がこの大きさを超えたら警告する（orientation_report_20260809 指定）。
# ハーネスは巨大出力を persisted-output へ退避するため、超過した list は
# 「exit 0 なのにデータがコンテキストに載っていない」沈黙失敗になる。
LIST_WARNING_BYTES = 200 * 1024

# orientation digest がこの大きさを超えたら警告を添える。**仮置き**——出所は従事中郎の
# 実測境界（20KB 台は載った／45.8KB・103.4KB は落ちた＝閾値は 25〜39KB 圏）の安全側下限で、
# 境界そのものはまだ特定されていない。追実測で校正する（LIST_WARNING_BYTES と同じ作法）。
# cc-defer: 実測下限の仮置き、載る最大値が追実測で特定できたらその値へ校正する
ORIENTATION_WARNING_BYTES = 25 * 1024


class RegistrySpec(NamedTuple):
    """管理表 1 表分の静的仕様（SSoT）。

    path の導出・キーフィールド・値オブジェクトの対応はすべてここから引く
    （`f"{name}_path"` のような文字列組み立てを散らさない）。
    """

    path_attr: str  # Config の path property 名
    key_field: str  # レコードの一意キー
    record_cls: type  # 検証に使う値オブジェクトクラス


# name -> RegistrySpec。wal_cli の kind -> key_field 導出と main.py の subparser 生成も
# ここを SSoT とする（表追加はこの dict に1行足すだけで CRUD/WAL/CLI が揃う）
REGISTRY_SPEC = {
    "individuals": RegistrySpec("individuals_path", "uuid", Individual),
    "tasks": RegistrySpec("tasks_path", "id", Task),
    "knowledge": RegistrySpec("knowledge_path", "id", Knowledge),
    # knowledge の直後＝orientation の表順でも索引と語彙表が隣接する（dict 順が表順）
    "subjects": RegistrySpec("subjects_path", "id", Subject),
    "abilities": RegistrySpec("abilities_path", "id", Ability),
    "profile": RegistrySpec("profile_path", "id", Profile),
    "goals": RegistrySpec("goals_path", "id", Goal),
    "steps": RegistrySpec("steps_path", "id", Step),
}


def registry_service(config: Config, name: str) -> RegistryService:
    """name の管理表に対する RegistryService を組み立てる（wal_cli と共有）。"""
    spec = REGISTRY_SPEC[name]
    return RegistryService(
        JsonRegistryStore(getattr(config, spec.path_attr)), spec.key_field
    )


def run_registry_command(
    config: Config, name: str, action: str, args: Any, sync=None
) -> int:
    spec = REGISTRY_SPEC[name]
    svc = registry_service(config, name)

    if action == "list":
        records = svc.list()
        payload = json.dumps(records, ensure_ascii=False, indent=2)
        print(payload)
        _warn_if_oversized(name, payload)
        _warn_if_unknown_keys(name, spec, records)
        return EXIT_OK

    if action == "get":
        rec = svc.get(args.key)
        if rec is None:
            print(f"not found: {name} {spec.key_field}={args.key}", file=sys.stderr)
            return EXIT_CONFIG_INVALID
        print(json.dumps(rec, ensure_ascii=False, indent=2))
        _warn_if_unknown_keys(name, spec, [rec])
        return EXIT_OK

    if action == "import":
        return _import_records(config, name, spec, svc, args, sync)

    if action == "add":
        try:
            raw = read_json_arg(args)
            _reject_invalid_write(config, name, spec, raw)
            vo = spec.record_cls.from_dict(raw)  # 値オブジェクトで検証
        except (ValueError, OSError, TypeError, KeyError) as exc:
            # wal_cli.run_wal_append と同一の捕捉タプル（入力不正は exit 2 に統一）。
            # json.JSONDecodeError は ValueError の子なので個別列挙しない
            print(f"invalid {name} record: {exc}", file=sys.stderr)
            return EXIT_CONFIG_INVALID
        record = vo.to_dict()
        svc.add_or_update(record)
        _sync_after_change(
            config, name, f"registry: add {name} {record[spec.key_field]}", sync
        )
        print(f"saved {name} {spec.key_field}={record[spec.key_field]}")
        return EXIT_OK

    if action == "remove":
        svc.remove(args.key)
        _sync_after_change(config, name, f"registry: remove {name} {args.key}", sync)
        print(f"removed {name} {spec.key_field}={args.key}")
        return EXIT_OK

    print(f"unknown action: {action}", file=sys.stderr)
    return EXIT_CONFIG_INVALID


def _import_records(
    config: Config,
    name: str,
    spec: RegistrySpec,
    svc: RegistryService,
    args: Any,
    sync,
) -> int:
    """--json / --json-file の全レコードを**全件検証してから一括置換**する（全件書き戻しの正面口）。

    1 件でも不正なら exit 2・無置換——部分書き込みは「どこまで入ったか」を運用者に数えさせる
    （`run_handoff_archive` の全件検証→全件移動と同型）。add の繰り返しでは「消えたレコード」
    を表現できないので、全件を配る側が持っている状態をそのまま反映する口を分けている。
    置換後の sync は一発（表は 1 ファイルゆえ何件でも 1 commit）。件数と増減は stderr へ
    ——stdout を汚さず、置換の規模だけは必ず目に入れる。
    """
    try:
        raw = read_json_arg(args)
        if not isinstance(raw, list):
            # add との取り違え（1 レコードの dict）を型エラーで転ばせず言語化する
            raise TypeError(
                f"import expects a JSON array of records, got {type(raw).__name__}"
            )
        # 語彙は batch で 1 回だけ引く（201 件の書き戻しで SUBJECTS を 201 回読まない）
        active = _active_subject_ids(config) if name == "knowledge" else set()
        records = []
        for row in raw:
            _reject_invalid_write(config, name, spec, row, active)
            records.append(spec.record_cls.from_dict(row).to_dict())
        _reject_duplicate_keys(spec, records)
    except (ValueError, OSError, TypeError, KeyError) as exc:
        # add と同一の捕捉タプル（入力不正は exit 2 に統一）
        print(f"invalid {name} import: {exc}", file=sys.stderr)
        return EXIT_CONFIG_INVALID

    existing = svc.list()
    before = {str(r.get(spec.key_field)) for r in existing}
    after = {str(r.get(spec.key_field)) for r in records}
    svc.replace_all(records)
    _sync_after_change(
        config, name, f"registry: import {name} ({len(records)} records)", sync
    )
    print(
        f"imported {name}: {len(existing)} -> {len(records)} records "
        f"(added: {len(after - before)}, removed: {len(before - after)})",
        file=sys.stderr,
    )
    return EXIT_OK


def _reject_invalid_write(
    config: Config,
    name: str,
    spec: RegistrySpec,
    raw: Any,
    active_subjects: set[str] | None = None,
) -> None:
    """書き込み口（add / import）だけの fail-closed 検証。read 経路には掛けない。

    `from_dict` は既知キーだけを転記するため、typo（`subjects` → `subject`）は例外にならず
    沈黙して消える。書き込みの手前で差集合を見て弾く——読み手が「登録したのに無い」を
    後から突き止める羽目にならない側に倒す。knowledge の `subjects` だけは追加で SUBJECTS の
    **active** な語彙と照合する（deprecated は既存レコードを壊さず新規付与だけ止める）。
    語彙はデータ（開いた語彙）ゆえ Interface が load し、判定は Domain 純関数に委ねる。
    `active_subjects` 未指定なら必要になった時だけ引く（add は 1 レコードゆえ遅延で十分、
    import は batch で 1 回引いた集合を渡す）。例外は呼び出し側の捕捉タプル
    （ValueError / TypeError）に乗って exit 2 へ翻訳される。
    """
    if not isinstance(raw, dict):
        raise TypeError(f"record must be a JSON object, got {type(raw).__name__}")
    unknown = unknown_keys(spec.record_cls, raw)
    if unknown:
        raise ValueError(f"unknown field(s): {', '.join(sorted(unknown))}")
    if name != "knowledge":
        return  # 主題の照合は knowledge 固有（他表は未知キー検証だけを共有する）
    subjects = [str(s) for s in raw.get("subjects") or []]
    if not subjects:
        return  # subjects 省略／空は従来どおり（SUBJECTS が空の環境でも add できる）
    active = _active_subject_ids(config) if active_subjects is None else active_subjects
    invalid = invalid_subjects(subjects, active)
    if invalid:
        # 弾かれる主体は自走エージェント——正しい語彙を並べないと自力で直せない
        raise ValueError(
            f"unknown subject(s): {', '.join(invalid)} "
            f"(active: {', '.join(sorted(active)) or '<none>'})"
        )


def _reject_duplicate_keys(spec: RegistrySpec, records: list[dict]) -> None:
    """import batch 内のキー重複を弾く（add 経路の upsert が担っていた一意性の代わり）。

    `replace_all` は渡された配列をそのまま保存するため、重複 id はそのまま表に残る——
    `get` は先頭だけを返し `remove` は両方消す、という「読みと書きで見え方が違う表」になる。
    レコード単位の検証では拾えない batch 固有の不正なので、置換の手前でここだけ見る。
    """
    seen: set[str] = set()
    duplicated: set[str] = set()
    for record in records:
        key = str(record.get(spec.key_field))
        if key in seen:
            duplicated.add(key)
        seen.add(key)
    if duplicated:
        raise ValueError(
            f"duplicate {spec.key_field}: {', '.join(sorted(duplicated))} "
            "(import replaces the whole table; each key must appear once)"
        )


def _active_subject_ids(config: Config) -> set[str]:
    """SUBJECTS の active な id 集合。語彙は**データ**ゆえ Domain 定数にしない。

    status 欠落は active 扱い（`Subject.from_dict` の既定と揃える）。表が無ければ空集合＝
    subjects 付きの add は全て弾かれるが、subjects を書かない従来の add は影響を受けない。
    """
    return {
        str(row.get("id", ""))
        for row in registry_service(config, "subjects").list()
        if str(row.get("status", "active")) == "active"
    }


def read_json_arg(args: Any) -> dict:
    """--json または --json-file から1レコードの dict を読む（wal_cli と共有）。

    両方未指定は明示メッセージの ValueError——json.loads(None) の TypeError に任せると
    「型エラー」という誤シグナルになるため、入力不正として言語化する
    （CLI 層の捕捉で EXIT_CONFIG_INVALID に翻訳される）。
    """
    if getattr(args, "json_file", None):
        with Path(args.json_file).open(encoding="utf-8") as f:
            text = f.read()
    elif getattr(args, "json", None):
        text = args.json
    else:
        raise ValueError("provide --json or --json-file")
    return json.loads(text)


def _sync_after_change(config: Config, name: str, message: str, sync) -> None:
    """管理表の変更後に git 同期（イベント駆動、R2-3）。

    sync 注入を優先（テスト/外部組み立て）、無ければ config から組み立てる
    （registry_sync_enabled 有効時のみ。無効なら no-op＝ローカルは git に触れない）。
    対象 path は REGISTRY_SPEC から引く（`f"{name}_path"` の文字列組み立てを廃し SSoT 化）。
    """
    service = sync if sync is not None else build_sync(config)
    if service is None:
        return
    path = getattr(config, REGISTRY_SPEC[name].path_attr)
    service.sync([path], message)


def _warn_if_oversized(name: str, payload: str) -> None:
    """list 出力が LIST_WARNING_BYTES 超なら stderr で警告する（fail-open）。

    stdout も exit code も変えない——退行リスクを持ち込まず、「気づけない」だけを潰す
    （run_registry_fetch の空表警告と同型の層3 可観測性）。警告にレコード内容は載せない
    （PII 非出力）ので、サイズと対処だけを言う。
    """
    size = len(payload.encode("utf-8"))
    if size <= LIST_WARNING_BYTES:
        return
    print(
        f"WARNING: {name} list output is {size} bytes (> {LIST_WARNING_BYTES}) — "
        "output this large can be diverted out of the agent's context while the "
        "command still exits 0. Use `orientation` for the startup digest, or "
        "`get --key` for a single record.",
        file=sys.stderr,
    )


def _warn_if_unknown_keys(name: str, spec: RegistrySpec, records: list[dict]) -> None:
    """未知キーを持つレコードがあれば stderr で告げる（read は fail-open、exit 0 のまま）。

    fail-closed は書き込み口（add / import）だけ——read に検証を掛けると、既存データの
    1 キーで起動時の list が全滅する（v1.8.0 Stage 1 で警戒した形）。ただし黙ると
    「import で弾かれるレコードが表に居る」ことに気づけないので、読めるまま声だけ出す
    （`_warn_if_oversized` と同型の層3 可観測性）。載せるのはキー名だけ——値は PII を
    含みうるので出さない。
    """
    unknown: set[str] = set()
    for row in records:
        if isinstance(row, dict):
            unknown |= unknown_keys(spec.record_cls, row)
    if not unknown:
        return
    print(
        f"WARNING: {name} has unknown field(s): {', '.join(sorted(unknown))} — "
        "they are dropped on read and rejected by `add` / `import` (fail-closed). "
        "Fix the records, or extend the value object if the field should be kept.",
        file=sys.stderr,
    )


def _report_orientation_size(digest: str) -> None:
    """orientation digest の総バイトを stderr へ常時 1 行申告する（fail-open）。

    `_warn_if_oversized` と違い**閾値未満でも黙らない**——安全側で黙る計器は、
    「exit 0 なのに digest がコンテキストに載っていない」を観測させないまま通す。
    サイズが毎枠見え続けることが、以後の絞り校正を自走させる材料になる。
    超過時だけ、退避の可能性と絞り方（実在のオプション名）を添える。
    stdout も exit code も変えない（digest 本文は byte 不変）。
    """
    size = len(digest.encode("utf-8"))
    print(f"orientation digest: {size} bytes", file=sys.stderr)
    if size <= ORIENTATION_WARNING_BYTES:
        return
    print(
        f"WARNING: orientation digest is {size} bytes (> {ORIENTATION_WARNING_BYTES}) — "
        "output this large can be diverted to persisted output while the command "
        "still exits 0, leaving the digest out of the agent's context. Narrow it with "
        "`--knowledge-latest` / `--notes-tail` / `--handoff-latest` / `--handoff-cap`.",
        file=sys.stderr,
    )


def _table_size(config: Config, name: str) -> int:
    """管理表ファイルの実バイト数（不在は 0＝初回起動でも orientation は完走する）。"""
    try:
        return getattr(config, REGISTRY_SPEC[name].path_attr).stat().st_size
    except OSError:
        return 0


def handoff_dir(config: Config) -> Path:
    """申し送りブロックの置き場。`archive/` サブディレクトリが卒業の受け皿になる。"""
    return config.artifacts_path / "handoff"


def _read_handoff_blocks(config: Config, limit: int) -> list[tuple[str, str]]:
    """`artifacts/handoff/*.md` を名前降順 `limit` 件だけ (ファイル名, 本文) で読む。

    非再帰 glob ＝ `handoff/archive/` 配下と非 .md は読まない（**卒業の受け皿の契約**、
    退行テストで固定）。中身は解釈しない（スキーマレス、DESIGN §3.10）——標準化するのは
    置き場と「辞書順ソート可能な命名」だけ。選択規則（名前降順）を UseCase の
    `pick_latest_handoffs` と共有するので、事前絞りは冪等に重なり出力は変わらない。
    不在・空は `[]`（no-op 完走）。読めない 1 ブロックで起動オリエンテーションを
    止めない（fail-open。結果が limit−1 件になるのは許容、stderr で告知する）。
    事前スライス後の 1 件不良は次点で繰り上げ補充しない——補充ループは handoff が
    ほぼ常に 0-3 件の現場に対して過剰（YAGNI）。
    """
    directory = handoff_dir(config)
    try:
        paths = sorted(directory.glob("*.md"), reverse=True)[: max(limit, 0)]
    except OSError:
        return []
    blocks = []
    for path in paths:
        try:
            blocks.append(
                (path.name, path.read_text(encoding="utf-8", errors="replace"))
            )
        except OSError as exc:
            print(f"handoff block unreadable ({path.name}): {exc}", file=sys.stderr)
    return blocks


def _option(args: Any, name: str, default: int) -> int:
    """argparse Namespace から orientation の数値オプションを解決する（未指定のみ既定値）。

    `getattr(...) or default` は falsy な `0` を未指定と同一視するため、最小方向の
    端点指定が最大側の既定に化けていた（絞るためのオプションが全通しの穴になる）。
    `is None` で分岐すれば `0` は UseCase の「非正＝全捨て」ゲートへそのまま届く。
    argparse 側は `default=DEFAULT_*` を持つので CLI 経由では常に値が来る——本ヘルパーは
    `args=None` 直呼び（テスト・プログラム呼び出し）のためのガード。
    """
    value = getattr(args, name, None)
    return default if value is None else value


def run_orientation(config: Config, args: Any = None) -> int:
    """起動時オリエンテーション用の絞り込みダイジェストを stdout に一撃出力する。

    全表を並べた一括 list（当時 7 表で 1.6MB）はハーネスの出力上限で退避され、データが
    コンテキストに載らないまま exit 0 する沈黙失敗を起こしていた。射影は UseCase の純ロジック、
    ここは stores（REGISTRY_SPEC のキー順＝表追加に自動追従）と実ファイルサイズ・
    handoff ブロックを注入する薄い配線に留める（read-only ゆえ git にも触れない）。
    出来上がった digest のサイズは stderr へ自己申告する——測れるのは組み上がった後だけ
    なので、build() の呼び出し元が計器を持つのが責務上も正しい（射影は純関数のまま）。
    """
    listers = {name: registry_service(config, name) for name in REGISTRY_SPEC}
    sizes = {name: _table_size(config, name) for name in REGISTRY_SPEC}
    handoff_latest = _option(args, "handoff_latest", DEFAULT_HANDOFF_LATEST)
    digest = OrientationService(listers, sizes).build(
        handoffs=_read_handoff_blocks(config, handoff_latest),
        notes_tail=_option(args, "notes_tail", DEFAULT_NOTES_TAIL),
        topic_width=_option(args, "topic_width", DEFAULT_TOPIC_WIDTH),
        handoff_latest=handoff_latest,
        handoff_cap=_option(args, "handoff_cap", DEFAULT_HANDOFF_CAP),
        knowledge_category=getattr(args, "knowledge_category", None),
        # 既定 None（全件／蓋なし）ゆえ `_option` は通さない——0 と未指定の区別は
        # getattr の default=None がそのまま担う（0 は UseCase 側で「全捨て」に届く）
        knowledge_latest=getattr(args, "knowledge_latest", None),
        knowledge_subject=getattr(args, "knowledge_subject", None),
        individuals_cap=getattr(args, "individuals_cap", None),
        abilities_cap=getattr(args, "abilities_cap", None),
        profile_cap=getattr(args, "profile_cap", None),
        goals_cap=getattr(args, "goals_cap", None),
        tasks_latest=getattr(args, "tasks_latest", None),
        steps_latest=getattr(args, "steps_latest", None),
    )
    print(digest)
    _report_orientation_size(digest)
    return EXIT_OK


def run_artifacts_sync(config: Config, sync=None) -> int:
    """`artifacts/` 配下を既存 sync 経路で commit & push（新規 git コードを書かない）。

    書き込み CLI は持たない——成果物の構造は秘書の判断（重要度の世界、DESIGN §3.10）。
    ここは「置かれたものを固定ブランチへ送る」決定論だけを担う。registry_sync 無効なら
    no-op exit 0（`_sync_after_change` と同型の後方互換）、`artifacts/` 未作成も no-op
    （存在しない path を `git add` に渡して失敗させない）。
    """
    service = sync if sync is not None else build_sync(config)
    if service is None:
        return EXIT_OK
    directory = config.artifacts_path
    if not directory.exists():
        print(f"artifacts-sync: nothing to sync ({directory} not found)")
        return EXIT_OK
    try:
        result = service.sync([directory], "artifacts: sync")
    except GitSyncError as exc:
        # 申し送りブロックはここを通らないと次枠に届かない＝失敗は伝えるべき事実。
        # スタックトレースを吐かず transient として返す（run_wal_push と同型）
        print(f"artifacts sync failed: {exc}", file=sys.stderr)
        return EXIT_FETCH_FAILED
    print(f"artifacts synced: committed={result.committed} pushed={result.pushed}")
    return EXIT_OK


def run_handoff_archive(config: Config, names: list[str], sync=None) -> int:
    """指名された handoff ブロックを `handoff/archive/` へ mv し、既存 sync で送る（卒業）。

    非再帰読みの契約（`_read_handoff_blocks`）が受け皿なので、移した時点で以後の
    orientation から外れる。**どれを卒業させるかは持たない**——消化（結晶化）を経た
    指名を受けるだけ（判断は重要度の世界、移動は決定論の世界）。名前は `handoff/` 直下の
    ファイル名そのもの（パス成分を含む入力は traversal として拒否、ops-rules §1）。
    全件検証してから全件移動する＝1 件でも落ちれば何も動かない（部分成功を作らない）。
    """
    directory = handoff_dir(config)
    archive = directory / "archive"
    sources = []
    # 重複指名は 1 回に畳む（2 度目の rename を FileNotFoundError で落とさない）
    for name in dict.fromkeys(names):
        if "/" in name or "\\" in name or Path(name).name != name:
            print(f"invalid handoff block name: {name!r}", file=sys.stderr)
            return EXIT_CONFIG_INVALID
        if not (directory / name).is_file():
            print(f"handoff block not found: {name}", file=sys.stderr)
            return EXIT_CONFIG_INVALID
        if (archive / name).exists():
            # POSIX の rename は黙って上書きする＝卒業済みブロックの消失。事前に止める
            print(f"handoff block already archived: {name}", file=sys.stderr)
            return EXIT_CONFIG_INVALID
        sources.append(name)

    archive.mkdir(parents=True, exist_ok=True)
    for name in sources:
        # 同一 FS 内の mv（git 側は rename として拾う＝履歴が切れない）
        (directory / name).rename(archive / name)
    print(f"archived {len(sources)} handoff block(s) to {archive}")
    return run_artifacts_sync(config, sync)


def run_role_status(config: Config) -> int:
    """PROFILE / GOALS から現在の役割（秘書/執事/コーチ/アネゴ）を決定論導出して JSON 1行で emit。

    起動時オリエンテーション（ROUTINE_PROMPT）が叩き、秘書は「今日の自分の顔」を知る。
    判定はコード（derive_role 純関数）、演じ方は SecretaryRole ガイダンス——LLM の役割自称を
    判定根拠にしない（DESIGN §3.11）。
    """
    profiles = registry_service(config, "profile").list()
    goals = registry_service(config, "goals").list()
    print(json.dumps(derive_role(profiles, goals).to_dict(), ensure_ascii=False))
    return EXIT_OK


def run_registry_fetch(config: Config, git=None) -> int:
    """起動時に固定ブランチから管理表を fetch（R2-3、ROUTINE_PROMPT が起動時に呼ぶ）。

    registry_sync 無効なら no-op（exit 0＝ローカル運用は git に触れない）。git 注入は
    テスト用、本番は config から GitCliAdapter を組み立てる。fetch 失敗は
    EXIT_FETCH_FAILED（transient、次回起動で再試行）。
    """
    if not config.registry_sync_enabled:
        return EXIT_OK  # no-op
    service = git if git is not None else build_git(config)
    try:
        service.fetch_checkout(config.registry_branch)
    except GitSyncError as exc:
        # 層3 可観測性: transient を沈黙して握り潰すと「気づけない空表稼働」になる。
        # 失敗の事実に加え、空表で継続＝記憶なし稼働という運用上の含意を警告で明示する
        # （principal への一報は ROUTINE_PROMPT 手順に委譲＝送信責務をコードに持たせない）。
        print(f"registry fetch failed: {exc}", file=sys.stderr)
        print(
            "WARNING: registry-sync is continuing with EMPTY tables — the secretary "
            "runs WITHOUT memory this session (all registry tables and any grants "
            "are unavailable until the next successful fetch). "
            "Treat registry reads as empty and notify the principal that memory is unloaded.",
            file=sys.stderr,
        )
        return EXIT_FETCH_FAILED
    print(f"registry fetched: {config.registry_branch}")
    return EXIT_OK
