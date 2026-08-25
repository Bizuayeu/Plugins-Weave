# Changelog

## [1.4.0] - 2026-08-25

静的チェックをワークスペース基準へ揃える。挙動の変更は無い（`path_resolver` の候補探索は
`os.path` から `pathlib` へ移ったが、優先順・戻り値の契約は不変）。

### Changed

- ruff の `select` に `N`（命名）と `PTH`（pathlib）を追加。既存の `C4` / `RUF` は残した
  ——ワークスペースの ToBe は二流儀の**和集合**であって置換ではない。`E` は `E4,E7,E9` へ
  絞り、`E501` は `ignore` から落として行長の判断を formatter へ一本化
- formatter をワークスペース既定へ（`line-length = 100` と `quote-style = "preserve"` を撤去
  ＝ 88 桁・クオート正規化）。11 ファイルが再整形された
- `path_resolver.get_plugin_root()` の候補リストを `list[Path]` へ統一
  （戻り値は元々 `Path(candidate)` だったので契約は不変）

### Fixed

PTH 22 件。**一様ではないので一括変換していない**:

- **`hooks/*.py` の 7 件は `per-file-ignores` で除外**（理由をコメントに明記）。候補パスは
  最終的に `sys.path.insert()` へ渡る。**`sys.path` の要素は str でなければならず**、`Path`
  を入れると import が黙って失敗する（実測: `ModuleNotFoundError`）。起動スクリプトなので、
  移植性より起動が成立することを取る
- **`hook_config.py` は `str()` で包んで変換**。`os.path.join(...).replace("\\", "/")` の
  `.replace` は **str のメソッド**であり、`Path.replace()` は引数 1 個の**リネーム操作**
  ——`Path` のまま繋ぐと意味が変わる（`settings.json` は "/" 区切りの文字列を要求する）
- **`file_io.py` / `path_resolver.py` は素直に変換**。前者の `tmp_path` は `mkstemp` 由来の
  str なので `Path(tmp_path)` で包んだ

### Notes

`path_resolver` のテスト 4 件は `path_resolver.os.path.isdir` を patch していたため、patch 先を
`Path.is_dir` へ移した。判定対象は候補パスの文字列のままで、各テストの意図（どの候補が
勝つか）は変えていない。

### 検証

ruff 22→0 ／ mypy Success ／ pytest 105 passed（前後一致）

## [1.3.1] - 2026-07-26

### Fixed

- `infrastructure/path_resolver.py::get_plugin_root()` と `hooks/emotion_writer_launcher.py` の候補探索に「自身の設置場所」を第3候補として追加。`~/DEV` も `~/.claude/plugins/marketplaces` も無い環境（CI runner 等、任意の場所への clone）で plugin root が解決できず launcher 系 4 件が失敗していた問題を解消。
- `pip install -e .` が flat-layout auto-discovery（`hooks` / `commands` を複数トップレベルパッケージと誤検出）でビルド失敗する問題を解消。`[tool.setuptools] packages = []` を明示（コード解決は `pythonpath = ["."]`、editable install は依存導入専用）。
- launcher の subprocess integration test が pytest-cov の instrumentation を子プロセスへ継承し、`Can't combine statement coverage data with branch data` で pytest を INTERNALERROR させる問題を解消（子の env から `COV_CORE_*` を除去）。

### Added

- CI に `test-emotionpulse` job を追加（Python 3.10 / 3.11 / 3.12 マトリクス、coverage XML アーティファクト）。
- `TestGetPluginRoot::test_returns_installed_location_when_named_candidates_missing` — 第3候補（自身の設置場所）へのフォールバックのユニットテスト。

## [1.3.0] - 2026-04-16

### Fixed

- Stop hookの`systemMessage`が Claude Code 本体で抜け落ちる問題 (#34600) を回避。`reason`フィールドに`systemMessage`全文を埋め込む fallback 実装。`systemMessage`も互換性のため残存。
- 他plugin（EpisodicRAG等）の cwd から`emotion_writer`が呼ばれた際の `scripts/application/__init__.py` モジュール解決衝突を解消。

### Added

- `hooks/emotion_writer_launcher.py` — 既存`stop_handler.py`と対称の launcher。`sys.path.insert(0, _plugin_dir)`で衝突回避。
- `infrastructure/path_resolver.py::get_plugin_root()` — DEV/marketplace両候補探索を一元化。
- `application/hook_config.py::get_launcher_path()` — launcher絶対パス解決。
- `scripts/tests/interfaces/test_emotion_writer_launcher.py` — launcher 構造 + subprocess integration test（conflicting cwd 下での動作確認）。
- `scripts/tests/infrastructure/test_path_resolver.py::TestGetPluginRoot` — 候補探索のユニットテスト。
- `scripts/tests/interfaces/test_stop_hook_handler.py` に reason fallback の regression test 3件追加。

### Changed

- `domain/constants.py::STOP_SYSTEM_MESSAGE` のplaceholderを`{writer_path}` → `{launcher_path}`。実行形式は`python "<launcher>" '{...}'` に。
- `application/hook_config.py::build_stop_hook_entry()` の候補探索を `get_plugin_root()` に委譲し重複排除。
- `application/hook_config.py::get_writer_path()` を削除（外部呼出なし、`get_launcher_path()`で代替）。
- `commands/setup.md` を plugin_dir 直接参照に刷新。`~/.claude/hooks/` への cp step を廃止し、`<plugin_dir>/hooks/stop_handler.py` を直接 settings.json に登録する方式へ移行。Architecture図に silent mode fallback と両 launcher を明示。config.json version を `1.3.0` に整合。

## [1.2.0] - 2026-04-04

### Changed

- Stop hook → メインエージェント自己評価アーキテクチャに移行
- command型Stop hookがsystemMessageで自己評価を指示
- ロックファイルによる二重発火防止（ralph-loop準拠）

### Added

- `/EmotionPulse:setup` — 対話式セットアップコマンド
- `domain/models.py`: HookLock（ロック状態管理）
- `interfaces/stop_hook_handler.py` — ロックベースblock/approve制御
- `interfaces/emotion_writer.py` — CLI引数→バリデーション→状態書き出し
- `hooks/stop_handler.py` — thin launcher
- `application/hook_config.py` — Stop hook設定エントリ生成
- `domain/constants.py`: LOCK_FILENAME, LOCK_MAX_AGE_SECONDS

## [1.1.0] - 2026-04-04

### Changed

- TaskCompleted hookアーキテクチャ（実験、後に廃止）

## [1.0.0] - 2026-04-04

### Added

- Initial release (Stop hook + claude -p)
