# Changelog

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
