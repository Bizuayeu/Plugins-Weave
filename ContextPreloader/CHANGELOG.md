# Changelog

## [1.1.0] - 2026-08-25 — 静的チェックの配線と os.path → pathlib 移行

本プラグインは CI が pytest しか回しておらず、ruff も mypy も持たなかった。規約はワークスペースの
**和集合**（同日確定）—— ruff の select を広く取り（書き方の危険を機械検出）、mypy は strict
（型の不整合を機械検出）。両者は直交しており、片方だけではどちらかが素通りする。

### Added

- `pyproject.toml`（新設）— `[tool.ruff]` / `[tool.mypy]` / `[tool.pytest.ini_options]`。**`[project]` /
  `[build-system]` は置かない**（配布物ではなく `python -m scripts` で起動されるフック実装で、
  設定を読む場所としてのみ要る）
- CI に `lint-contextpreloader` / `type-check-contextpreloader` ジョブ（ruff check・
  ruff format --check・mypy strict）。ルールの正典は pyproject で、YAML には書かない

### Changed

- **lint 診断 124 → 0。** うち **73 件が `os.path` → `pathlib` 移行**（`PTH108` 37 / `PTH123` 18 /
  `PTH118` 7 ほか）、`SIM115` 11 件を `with` 化（Windows では閉じ漏れハンドルが後続の open を
  実際に塞ぐ）、`SIM102` / `E741` ほか
- **mypy strict 158 → 0。** 119 件は `-> None` の付与、ヘルパー 4 本の型付けで `no-untyped-call`
  13 件が連鎖で解消、裸の `dict` に型引数
- `ruff format` を適用（25 files）

### Fixed

- **`B904` 6 件 — `except` 節で例外連鎖が切れていた**（`config_repository` 2 / `file_reader` 4）。
  `raise ... from e` を置き、元の例外のトレースバックが失われる経路を塞いだ
- ⚠️ **移行作業そのものが本番バグを 1 件生み、実測で捕まえた。** `os.path.join` → `Path(a) / b` は
  戻り値を str から Path に変える。`hooks` の `_CANDIDATE_PATHS` はそのまま `sys.path.insert()` へ
  渡っており、**`sys.path` は Path を受け付けない**（実測: `ModuleNotFoundError`）。フックのパス解決は
  unit test が踏まないので pytest は素通りしていた。`str()` を戻し理由をコードに残した。
  同型の型ズレ 11 件は **strict mypy が検出**——lint と型が直交していることの実例

### Tests

- **112 passed — 作業前後で完全一致。** 加えてフックを実起動して exit 0 を確認（env 経由・既定パスの
  両方）、`python -m scripts list` も exit 0

---

## [1.0.0] - 2026-03-24

### Added

- SessionStart hook（`hooks/context_preloader.py`）— セッション開始時に任意のファイル・URL を事前文脈として読み込む。claude.ai のプロジェクト機能を Claude Code 上で再現する。
- `sources.json` による読み込み対象の宣言（`id` / `label` / `path` / `type` / `enabled` / `priority` / `description`）。設置先は `~/.claude/plugins/.contextpreloader/`、雛形は `.claude-plugin/sources.template.json`。
- プロファイル合成（`application/profile_merger.py`）— 環境ごとの上書きを `profile.json` で重ねる。雛形は `.claude-plugin/profile.template.json`。
- `settings` による挙動制御 — `encoding` / `max_lines_per_file` / `show_summary` / `url_timeout` / `mode`。
- ソース種別の自動判定（`domain/detection.py`、`type: "auto"`）と、ファイル読込・URL 取得の両経路（`infrastructure/file_reader.py` / `url_fetcher.py`）。
- `/context-preload` コマンド — ソースの追加・削除・テスト・プロファイル管理の入口。
- 開発時にプラグインパスを上書きする環境変数 `CONTEXTPRELOADER_PLUGIN_DIR`。
- Clean Architecture 構成（domain / application / infrastructure / interfaces）と各層のテストスイート。
