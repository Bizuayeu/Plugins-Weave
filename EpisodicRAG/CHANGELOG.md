[English](CHANGELOG.en.md) | 日本語

# Changelog

All notable changes to EpisodicRAG Plugin will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## 目次 / Table of Contents

- [v5.x](#583---2026-07-29)
- [v4.x](#410---2025-12-03)
- [v3.x](#330---2025-11-29)
- [Archive (v2.x以前)](#archive-v2x-and-earlier)
- [バージョニング規則](#バージョニング規則)

---

## [5.8.3] - 2026-07-29

### Changed

- **CI を二層に分離（常設ゲートの決定論化）** — メイン coverage job の pytest に `-m "not slow and not performance"` を追加し、壁時計アサートを持つテスト群を既設の performance 専用 job（`-m "slow or performance" --no-cov`）へ一本化した。常設ゲートは決定論的に検査できるものだけを検査する形になり、共有ランナーの負荷で CI が確率的に赤くなる事象（v5.9.8 リリース時に実発生）が構造的に消える。同じテストの二重実行も解消。TEST_COUNT バッジの件数はメイン job の選択分（slow / performance を除いた分）を表す
- **絶対スループットアサートを格下げ** — `test_scale.py` の `> 50 files/sec` / `> 100 ops/sec`（マシン性能そのものを検査していた 2 本）を撤去し、merge 結果・生成ファイルの正当性アサート + スループットの `print` に置き換えた。検査対象を「速さ」から「正しさ」へ移し、数値は情報として残す。上限系（`elapsed < N`）は性能回帰の網として温存
- **TESTING.md / scripts/README.md を二層運用へ追従** — マーカー説明（`performance` はメイン job で除外される、が実態として真になった）・CI 節・ローカル実行の役割分担・カバレッジ目標・Performance Targets の位置付け（CI が保証する値ではない参考目標）を実態化。併せて `pyproject.toml` 未登録で `--strict-markers` 下では使えなかった `fast` マーカーの記述を削除

---

## [5.8.2] - 2026-07-29

### Changed

- **バージョンバッジを dynamic badge 化（同期作業の構成的排除）** — README 日英・`docs/README.md` のバージョンバッジを shields.io の dynamic JSON バッジへ置換し、SSoT（`.claude-plugin/plugin.json` / ルートは `marketplace.json`）を表示時に読ませる。バッジから実数字が消えたため、bump 時の手動同期そのものが無くなった（v5.9.8 bump で同期漏れにより CI が赤くなった事象への恒久対処）
- **整合テストを「数字の一致」から「指し先の検査」へ転換** — `test_version.py` のバッジ検査が、dynamic badge の `url=` が正しい SSoT を、`query=` が `$.version` を指すことを検査する形に変更。併せて静的バッジ（`badge/version-x.y.z-`）の不存在を恒久ゲートとして検査し、EpisodicRAG README 日英の検査（従来 pytest 無検査だった箇所）を新設
- **CONTRIBUTING 日英のリリース手順を更新** — バージョン同期表からバッジの手動同期を削除し、リリース手順を 5 ファイル → 4 ファイルへ（バッジは自動追従）

---

## [5.8.1] - 2026-07-25

### Changed

- **DigestAnalyzer に `effort: high` を明示** — 分析の深さが Digest の品質を直接決める層のため、呼び出し元の設定を継ぐのではなく frontmatter で思考量を固定する（`model: opus` は据え置き）

---

## [5.8.0] - 2026-07-25

### Added

- **wakeup: `materialize` / `verify` サブコマンド（配置ドリフトの根絶と fail-open の封鎖）**
  - **背景**: ★ 配置物（config / directive / token）は手コピー運用で、config と directive が別々に持ち回されるため「**directive だけ新しく config は旧世代**（`commit_identity.coauthor` が旧モデル名のまま書き戻される）」というドリフトが実運用で発生した。加えて Step 3 は md の Read ゆえ、directive 未配置でも黙って通る fail-open だった
  - `materialize --config <path> --out <dir> [--token <path>]`: 人格の config を**単一 SSoT** とし、directive は**その隣**から `directive_path` で解決して配置。config → `wakeup.config.json`（固定の汎用名）、token は元の basename のまま（勝手なリネームをせずケース不一致を防ぐ）。**全検証を全コピーの前**に実行し、半端に materialize された skill root を作らない。人格名は engine に持たせない path 駆動（`examples/` は見本のまま、他人格の値が repo に入らない）
  - `verify [--root <dir>]`: config / directive / token の実在・可読性を検査して非ゼロ終了。`config` 行に load_repo の fingerprint を出力（**1 デプロイ ＝ 1 人格**ゆえ、別人格の config を上げたままの起動事故を検知）。token は可読性のみ検査し中身は一切出力しない
  - Clean Architecture: 検証方針は UseCase（`usecases/verify_deployment.py` ＋ `DeploymentProbePort`）、ファイル配置は Interface（engine）。TDD（wakeup は 61 → 132 tests）
- **CI に wakeup スキルを追加** — 既存 EpisodicRAG ジョブへ ruff check / ruff format --check・bandit・mypy strict・pytest の 4 系統を追加（従来はローカル実行のみでテスト腐敗のリスクがあった）。workflow 自身の変更も CI トリガに追加

### Changed

- **`directive_path` の構造検証を domain へ** — 相対・POSIX 区切り・親脱出なし・空セグメントなしを `WakeupConfig.__post_init__` で強制。人格が任意の名前・深さを選べる前提は保ったまま、skill root 外への解決を封じる
- **SKILL.md**: 「デプロイ（zip 化の直前）」節を新設、Step 1 を config 読込から**デプロイ検証（verify）**へ変更、「1 デプロイ ＝ 1 人格」「器交代時に更新する config キー ＝ `commit_identity.coauthor`」を明記
- **pyproject**: ruff の `include` に `skills/wakeup/scripts/**/*.py`、isort `known-first-party` に `usecases` を追加（スキル配下が lint 対象外だった）。当該ツリーへ `ruff format` を初適用

### Fixed

- **config 検証の抜け穴** — `load_config` が `WakeupConfig` を try の**外**で構築していたため、domain の `ValueError` が `ConfigError` に包まれず素通りしていた（単一エラー面の破れ）
- **tar アーカイブの非正規メンバー** — `extractfile()` の `None` を未処理で `.read()` していた（mypy strict で検出、明示エラーに）

---

## [5.7.0] - 2026-07-02

### Added

- **update_shadow_overall CLI（SGD overall_digest 更新の interface 化）** — ShadowGrandDigest の overall_digest 5要素（digest_type / keywords / abstract / impression / timestamp）を JSON 入力から更新する `interfaces/update_shadow_overall.py` を新設
  - **背景**: overall_digest の abstract は 2400 字級の日本語文字列を含み、Edit ツールの exact-match 置換による手動更新は事故りやすい。ShadowIO 経由の JSON ラウンドトリップで安全に更新する
  - `source_files` には触れない（不変条件）。`timestamp` / `metadata.last_updated` は自動更新
  - 入力バリデーション: 必須4キー・型検査。エラー時 SGD は変更されない
  - 使用法: `python -m interfaces.update_shadow_overall <level> <json_file>`（`--stdin` 対応）

### Changed

- **`/digest` の SGD 統合更新手順を CLI 化** — Pattern 1 Step 7 / Pattern 2 Step 6・Step 8.5 の「Edit ツールで各フィールドを更新」を、一時ファイル + `update_shadow_overall` 実行の手順に変更（`commands/digest.md`）。source_files フォーマット規約（1行ずつ）は Pattern 1 Step 3 へ移設

### Fixed

- **Windows cp932 コンソールでのログクラッシュ** — `logging.StreamHandler` の出力先が cp932（リダイレクト・パイプ時の既定）だと、digest_type に頻出する em-dash「——」(U+2014) が `UnicodeEncodeError`（`--- Logging error ---`）を引き起こしていた。`setup_logging()` がハンドラーの stream を UTF-8 の `TextIOWrapper` で包み直すよう修正（`_utf8_safe_stream()`、handler-local な差し替えで `sys.stdout` 自体は変更しない）
  - 副次効果: パイプ環境で文字化けしていた日本語ログが可読になった
  - テスト: `test_logging_config.py::TestHandlerEncodingSafety`（cp932 疑似コンソールで内容到達まで検証）

---

## [5.6.0] - 2026-06-14

### Added

- **dream-defrag コマンド（引く dream＝auto-memory の GC）** — `/digest` Step 11 の Auto-dream（足す dream＝additive enrichment）と対をなす、Claude Code auto-memory（`MEMORY.md` + `memory/*.md`）の reductive な棚卸し
  - memory-dream の 4 フェーズのうち **③Dedup & Resolve（横断重複統合）・④Prune & Index（完了卒業・index lean 化）** を担う（①Mine・②Consolidate は Step 11 の責務）
  - サブコマンド: `scan`（件数診断・`DEFRAG_THRESHOLD=50` 超過判定）/ `snapshot`（剪定前バックアップ）/ `rebuild-index`（`MEMORY.md` をディスク現存に同期、`--preview` 対応）
  - **判断と決定論の分離**: スクリプトは件数集計・snapshot・索引同期の決定論のみ。何を重複/卒業/上位層DRY と見て剪定するかの判断は Claude が `commands/dream-defrag.md` のフローで担う
  - **安全要件**: auto-memory は git 非追跡で revert 不能なため、剪定前 snapshot を必須化。非破壊フロー（snapshot → 候補提示 → ユーザー裁可 → 適用）。snapshot は走査対象 dir の外（永続化 dir 配下 `snapshots/`）に作成
  - **卒業の境界**: 完了プロジェクトは `MEMORY.md` live index からの降格に限定し、EpisodicRAG（Loops/Digests）への実記録は行わない（記憶層は不可侵）。未記録なら削除せずフラグ
  - Clean Architecture（Domain / UseCase / Interface / Infrastructure）＋ TDD（24 tests: defrag 型・DefragScanner 件数判定・snapshot・index round-trip・CLI subcommand）

### Architecture

- 既存 `auto_dream` パッケージ内に同居（新パッケージは切らない）: `domain/auto_dream/defrag_types.py`, `application/auto_dream/defrag_scanner.py`, `infrastructure/auto_dream/{snapshot_writer,index_writer}.py`, `interfaces/dream_defrag.py`

---

## [5.5.0] - 2026-05-31

### Added

- **wakeup スキル（claude.ai セッション開始エンジン）** — claude.ai でセッション開始時に長期記憶ロード＋人格ディレクティブ適用を担う汎用エンジン
  - 「汎用エンジン（scripts/）＋ ペルソナ固有値（examples/）」を分離。リポ名・ファイル・commit identity・人格方針はすべて config 注入（決め打ちなし、lint で保証）
  - 配置物は人格名を含まない汎用名に固定（実行時 config = `wakeup.config.json`、directive 名のみ config の `directive_path` 経由で可変）。ペルソナ固有のサンプルは `examples/`（`weave.config.json` 等）に隔離し、実行時パスへの固有名リークを lint で検出
  - Clean Architecture（Domain / UseCase / Interface）＋ TDD（59 tests: 値オブジェクト・BootSequence・config ローダ・engine・SKILL.md lint〔配置物の汎用名・固有名リーク検証を含む〕）
  - 記憶ロードは Read token で SHA 固定取得（claude.ai 共有 IP では未認証 API が枯渇、raw の main は CDN キャッシュで最新が取れないため）
  - Private 参照／書き戻し（`claude/*` → PR）に対応。token は tar.gz でスキル同梱（claude.ai はネスト zip 不可のため）、Authorization ヘッダのみで URL 非露出
  - 表情 UI は担当しない（VisualExpression スキルと相互参照なし）。両スキルとも単体で完結し、claude.ai のプロジェクト指示で独立に有効化する設計

---

## [5.4.0] - 2026-05-01

### Changed

- **auto_dream_scan の出力責務を「メモリ所在通知」に絞り込み（案B運用への移行）**
  - `MemoryFile` から `content` / `content_length` を除去
  - `MemoryIndex` から `raw_content` を除去
  - 出力サイズ 68KB → 12.3KB（5.4倍縮減）、Claude Code preview の切り詰め問題が解消
  - Claudeは MEMORY.md と各 frontmatter.description で関連性を判定し、関連メモリだけを `path` から個別Readで取得して digest 内容と突合する運用へ
  - `commands/digest.md` の Step 11 を案B運用ガイダンスに刷新

### Fixed

- **hypothesis FailedHealthCheck in test_template_properties.py**
  - `valid_levels` strategy の `whitelist_categories=("L", "N")` は Lo（CJK等）を含み生成候補が数十万となり、Input generation が遅くなって FailedHealthCheck を発火していた
  - `("Ll", "Lu", "Nd")` + `whitelist_characters="_"` に絞り、ASCII 英数字+_ に限定
  - 実行時間 242秒 → 5.80秒（13/13 pass）

### Internal

- TypedDict 構造検証 / 戻り値検証 / scanner結果検証のテスト9件追加
- domain/auto_dream/types.py、infrastructure/auto_dream/memory_reader.py、interfaces/auto_dream_scan.py の docstring を新責務に合わせ更新

---

## [5.3.0] - 2026-03-26

### Added

- **Auto-dream: メモリ棚卸し機能**
  - digest処理のStep 11として、Claude Code auto-memoryファイルの自動スキャン・棚卸しを追加
  - `python -m interfaces.auto_dream_scan` CLIで実行可能
  - `~/.claude/projects/*/memory/` 配下のメモリファイルを検出・解析
  - frontmatter（name, description, type）の自動パース（PyYAML不使用、依存ゼロ維持）
  - Pattern 1（新Loop検出）・Pattern 2（階層確定）の両方で動作
  - メモリ未使用環境では自動スキップ（graceful degradation）

### Architecture

- **新規パッケージ**: `domain/auto_dream/`, `infrastructure/auto_dream/`, `application/auto_dream/`
- Clean Architecture 4層に準拠（Domain → Infrastructure → Application → Interfaces）
- テスト46件追加（domain: 12, infrastructure: 34, application: 8, interfaces: 5）

---

## [5.2.0] - 2025-12-14

### Changed

- **永続化パス**
  - config.json と last_digest_times.json を `~/.claude/plugins/.episodicrag/` に移動
  - Claude Codeのプラグイン自動更新（削除→再clone）時に設定が消失しなくなりました
  - 環境変数 `EPISODICRAG_CONFIG_DIR` でカスタムパスを指定可能（テスト用）

### Added

- **内部リファクタリング（TDD改善）**
  - `digest_auto.py` を `digest_auto/` パッケージに分割（548行→5モジュール: models, analyzer, path_resolver, file_scanner, report）
  - `CascadeComponents` パラメータオブジェクト追加（Parameter Object Pattern）
  - シングルトンモジュール（`level_registry`, `error_formatter`, `file_naming`）のdocstringにリセット方法を明記

### Documentation

- **INDEX.md / INDEX.en.md 新規作成**
  - 全ドキュメントへのナビゲーション
  - 読者別ガイド（初心者/日常利用/トラブル時/開発者/AI向け）
  - ドキュメント更新時のチェックリストとしても機能

- **CLAUDE.md 改善**
  - 「利用可能な機能」セクション追加（コマンド/スキル/エージェント/基本ワークフロー）
  - AIが初見でもプラグインを使えるように

- **ドキュメント構成整理**
  - `_footer.md` をフッターSSoTのみに簡素化
  - 各READMEからINDEX.mdへのリンク追加

> 📖 詳細は [DESIGN_DECISIONS.md](docs/dev/DESIGN_DECISIONS.md) を参照

---

## [5.1.0] - 2025-12-07

### Changed

- **digest.md リファクタリング**
  - パターン2を7ステップ→9ステップに再構成
  - 目次をパターン別に分離（読み飛ばしやすく）
  - 「出力例」→「エラー出力例」に改名（成功例は各Step 9へ移動）

- **スキルドキュメント改善**
  - 各SKILL.mdにTodoWrite使用ガイドを追加
  - スキルドキュメント構造を共通化
  - 使用例・出力例を最新化

---

## [5.0.0] - 2025-12-05

> **⚠️ 移行について**: v4.x以前からの移行は非推奨です。プラグインの再インストールを推奨します。
> 既存の対話記録（GrandDigest, ShadowGrandDigest, Loopファイル等）はそのまま使用できます。

### Breaking Changes

- **プラグインルート自動検出**
  - `/digest` 実行時の `config.json` 検出エラーを防止
  - 任意のディレクトリから `/digest` を実行可能に

- **Loopレベル追加**
  - `last_digest_times.json` に Loop 層を追加
  - 全レベル（Loop含む）で最新の `/digest` 対象を把握可能に

- **シェルスクリプト廃止**
  - 対話型プロセスを md ファイルに一本化
  - 目的: 可読性向上、読み飛ばし防止

### Added

- **Bandit セキュリティスキャン統合**
  - `make security` でセキュリティ脆弱性をスキャン
  - CI/CD (GitHub Actions) に security ジョブ追加
  - pre-commit フックに Bandit 追加
  - 統合テスト `test_bandit_integration.py` 追加

- **cascade_orchestrator 可読性向上**
  - 4ステップ制御フローのコメント追加
  - `CascadeStepResult.details` の構造説明追加

---

## [4.1.0] - 2025-12-03

### Added

- **CONCEPT.md / CONCEPT.en.md**: コンセプトドキュメント新規作成（日英同期 210行/210行）

- **内部リファクタリング**: TypedDict分割、Literal型導入、CLI共通ヘルパー統合、バリデーション統合、新デザインパターン4種追加

- **開発ツール**: フッターチェッカー、リンクチェッカー（`scripts/tools/`）

> 📖 詳細は [DESIGN_DECISIONS.md](docs/dev/DESIGN_DECISIONS.md) を参照

---

## [4.0.0] - 2025-12-01

> **⚠️ 移行について**: v3.x以前からの移行は非推奨です。プラグインの再インストールを推奨します。
> 既存の対話記録（GrandDigest, ShadowGrandDigest, Loopファイル等）はそのまま使用できます。

### Breaking Changes

- **config層のClean Architecture分解**: 単一configモジュールを3層に再編成
  - `domain/config/` - 定数・型検証
  - `infrastructure/config/` - ファイルI/O・パス解決
  - `application/config/` - バリデーション・サービス
  - **移行**: インポートパスを層構造に合わせて更新

- **スキルのPythonスクリプト化**: 疑似コードから実行可能CLIへ
  - `@digest-setup` → `python -m interfaces.digest_setup`
  - `@digest-config` → `python -m interfaces.digest_config`
  - `@digest-auto` → `python -m interfaces.digest_auto`
  - スキル経由の使用は引き続き可能

- **trusted_external_pathsの導入**: 外部パスアクセスのセキュリティ強化
  - config.jsonに `trusted_external_paths: []` フィールド追加
  - 外部パス使用時は明示的なホワイトリスト登録が必要

---

## [3.3.0] - 2025-11-29

### Added

- **LEARNING_PATH.md**: Python学習ドキュメント追加
  - Clean Architecture学習の段階的パス
  - EpisodicRAGコードベースを教材としたPython学習ガイド

### Changed

- **バージョンSSoT強化**: CONTRIBUTING.mdのバージョン例をプレースホルダー化
  - ハードコードされたバージョン番号を `x.y.z` に変更
  - plugin.jsonへの参照を明示化

- **英語版ドキュメント同期**: syncヘッダー追加
  - README.en.md, EpisodicRAG/README.en.md
  - QUICKSTART.en.md, CHEATSHEET.en.md
  - CONTRIBUTING.mdの規定に準拠した `<!-- Last synced: YYYY-MM-DD -->` 形式

---

## [3.2.0] - 2025-11-29

### Added

- **FAQ.md**: GitHub検索機能での横断検索ガイドを追加
  - リポジトリ内検索（GitHub Web）の案内
  - ローカル検索（VS Code）の案内
  - 用語インデックスへの参照

- **TESTING.md**: テストドキュメント拡充
  - GitHub Actions CI/CDバッジ追加
  - Codecovカバレッジレポートへのリンク追加
  - 層別テストファイル一覧表追加
  - カバレッジ目標表追加
  - ローカルカバレッジ実行コマンド追加

- **api/domain.md**: 主要TypedDictの完全スキーマを追加
  - ConfigData（config.json全体構造）
  - ShadowDigestData（ShadowGrandDigest.txt全体構造）
  - GrandDigestData（GrandDigest.txt全体構造）
  - RegularDigestData（確定済みDigestファイル）
  - IndividualDigestData（個別ダイジェスト要素）
  - TypeScript形式でスキーマを表現

---

## [3.1.0] - 2025-11-29

### Added

- **DESIGN_DECISIONS.md**: 設計判断ドキュメントを新規作成
  - Clean Architecture採択理由
  - デザインパターン選択の根拠（Facade, Repository, Strategy, Builder, Singleton, Template Method, Factory）
  - Pythonプログラミング教材としての価値向上を目的

- **CHEATSHEET.md / CHEATSHEET.en.md**: クイックリファレンスを新規作成
  - コマンド・スキル早見表
  - ファイル命名規則
  - デフォルト閾値
  - 日常ワークフロー
  - 日英完全同期（91行/91行）

### Changed

- **ドキュメントSSoT強化**: 包括的なSSoT参照リファクタリング
  - ADVANCED.md: SSoT参照3箇所追加（記憶構造、8階層構造）
  - QUICKSTART.md/en.md: SSoT参照追加、日英完全同期（179行/179行）
  - API_REFERENCE.md: 「使い方」セクション追加、DESIGN_DECISIONS参照
  - ARCHITECTURE.md: DESIGN_DECISIONS参照追加
  - CONTRIBUTING.md: DESIGN_DECISIONS参照追加
  - README.en.md: Path Format Differencesセクション追加（日英同期 380行/380行）
  - FAQ.md: 参照パス修正、CHEATSHEET参照追加
  - GUIDE.md: CHEATSHEET参照追加

- **デザインパターンの明示化**: API_REFERENCE.mdにパターン一覧を追加
  - Facade, Repository, Singleton, Strategy, Template Method, Builder, Factory

---

## [3.0.0] - 2025-11-28

### Breaking Changes

- **Loop IDの桁数変更**: 4桁→5桁
  - 旧形式: `Loop0001`
  - 新形式: `L00001`
  - **移行方法**: 既存Loopファイルのリネームが必要
    ```bash
    # 例: L0001_xxx.txt → L00001_xxx.txt
    cd your_loops_directory
    for f in L[0-9][0-9][0-9][0-9]_*.txt; do
      mv "$f" "L0${f:1}"
    done
    ```
  - **影響範囲**:
    - Loopファイル名
    - ShadowGrandDigest.txt 内の `source_files` 参照
    - last_digest_times.json 内の参照

- **ドキュメントの完全SSoT化**: 用語定義はREADME.mdに一元化
  - ユーザーへの影響なし（ドキュメント構造の改善のみ）

- **テストスイートの導入**: pytest + hypothesis によるプロパティベーステスト
  - 開発者向け変更、エンドユーザーへの影響なし

### Changed

- バージョン管理の全ファイル同期

---

<details id="archive-v2x-and-earlier">
<summary>Archive (v2.x and earlier)</summary>

## [2.3.0] - 2025-11-28

### Breaking Changes

- **config/__init__.py: 後方互換性用の再エクスポートを完全削除**
  - `extract_file_number`, `extract_number_only`, `format_digest_number` → `domain.file_naming`から直接インポート
  - `ConfigData`, `LevelConfigData` → `domain.types`から直接インポート

  ```python
  # 旧（動作しない）
  from config import extract_file_number, ConfigData

  # 新（推奨）
  from domain.file_naming import extract_file_number
  from domain.types import ConfigData
  ```

---

## [2.2.0] - 2025-11-28

### Changed

- **型安全性向上**: `Dict[str, Any]` → `ConfigData` (TypedDict) への移行
  - `config/path_resolver.py`: パラメータ型を `ConfigData` に変更
  - `config/threshold_provider.py`: パラメータ型を `ConfigData` に変更
- **config/__init__.py リファクタリング**:
  - domain定数の再エクスポートを削除（直接 `from domain.constants import ...` を使用）
  - 初期化パターンを即時初期化に統一（遅延初期化を廃止）
  - ローカルインポートをモジュールレベルに移動
- **infrastructure/json_repository.py**: エラーハンドリングを `_safe_read_json()` ヘルパー関数に共通化
- **反復プロパティの動的化**:
  - `ThresholdProvider`: `__getattr__` を使用した動的プロパティアクセス
  - `DigestConfig`: threshold委譲を動的化

### Added

- **GrandDigestManager のユニットテスト追加** (11件):
  - `get_template()` の構造・バージョン・レベル検証
  - `load_or_create()` の新規作成・既存読み込み・破損ファイル処理
  - `update_digest()` の正常更新・レベル保持・タイムスタンプ更新
- **`__all__` エクスポートの追加**:
  - `config/path_resolver.py`
  - `config/threshold_provider.py`
  - `infrastructure/json_repository.py`
  - `infrastructure/logging_config.py`
  - `application/shadow/cascade_processor.py`
- `agents/README.md` にフッターを追加

### Fixed

- `config/__init__.py`: ローカルインポート (`show_paths` メソッド内) をモジュールトップレベルに移動
- インポートパスの統一: `from config import LEVEL_CONFIG` → `from domain.constants import LEVEL_CONFIG`

---

## [2.1.0] - 2025-11-27

### Changed

- **DEPRECATED メソッド完全削除**:
  - `load_or_create`, `save`, `find_new_files` を削除

### Added

- **型安全性向上**:
  - `ProvisionalDigestFile` 型追加
  - `provisional_loader.py`, `save_provisional_digest.py` の型置換
  - `Dict[str, Any]` 使用箇所を汎用関数のみに限定

---

## [2.0.1] - 2025-11-27

### Changed

- **ログ統一**: `print` → `logger` に全面置換
- **Facade簡潔化**: public APIを整理（DEPRECATED 3メソッド）

### Added

- **テストカバレッジ拡大**
- **型定義統一**: `DigestMetadataComplete` 追加

### Fixed

- `cascade_processor.py`: 型チェック漏れ修正

---

## [2.0.0] - 2025-11-27

### Breaking Changes

**Clean Architecture リファクタリング完了** - 内部構造を4層アーキテクチャに全面移行

- **後方互換性レイヤー削除**: 旧インポートパス（`from validators import ...`, `from finalize_from_shadow import ...`等）は動作しなくなりました
- **推奨インポートパス変更**:
  ```python
  # 旧（動作しない）
  from validators import validate_dict
  from finalize_from_shadow import DigestFinalizerFromShadow

  # 新（推奨）
  from application.validators import validate_dict
  from interfaces import DigestFinalizerFromShadow
  ```

### Added

- **Clean Architecture 4層構造**:
  - `domain/` - コアビジネスロジック（定数、型、例外、ファイル命名）
  - `infrastructure/` - 外部関心事（JSON操作、ファイルスキャン、ロギング）
  - `application/` - ユースケース（Shadow管理、GrandDigest管理、Finalize処理）
  - `interfaces/` - エントリーポイント（DigestFinalizerFromShadow, ProvisionalDigestSaver）

- **テスト大幅拡充**:
  - 新規テストファイル追加
  - 全テストが新アーキテクチャに対応

- **ドキュメント更新**:
  - ARCHITECTURE.md - 4層構造の詳細説明追加
  - API_REFERENCE.md - 層別に再構成
  - scripts/README.md - 4層構造に全面更新
  - CONTRIBUTING.md - 新機能追加ガイド追加

### Changed

- **依存関係の明確化**: 循環参照を解消し、層的依存関係を確立
  - `domain/` ← 何にも依存しない
  - `infrastructure/` ← domain/ のみ
  - `application/` ← domain/ + infrastructure/
  - `interfaces/` ← application/

### Removed

- **後方互換性レイヤー削除**:
  - `scripts/finalize/`
  - `scripts/shadow/`
  - ルートレベルファイル: `validators.py`, `digest_times.py`, `grand_digest.py`, `shadow_grand_digest.py`, `finalize_from_shadow.py`, `save_provisional_digest.py`, `__version__.py`, `digest_types.py`, `exceptions.py`, `utils.py`

### Migration Guide

開発者向け移行ガイド:

1. **インポートパスの更新**:
   ```python
   # Domain層
   from domain import LEVEL_CONFIG, __version__, ValidationError
   from domain.file_naming import extract_file_number

   # Application層
   from application.shadow import ShadowUpdater
   from application.grand import ShadowGrandDigestManager

   # Interfaces層
   from interfaces import DigestFinalizerFromShadow
   from interfaces.interface_helpers import sanitize_filename
   ```

2. **詳細**: ARCHITECTURE.md および scripts/README.md を参照

---

## [1.1.8] - 2025-11-27

### Added
- **CLAUDE.md**: プロジェクト固有のAIエージェント向けガイドライン
  - SSoTの場所と参照パターン
  - 開発ワークフローとコーディング規約
  - 用語統一ルール（Loop, Digest, GrandDigest）
- **バックアップ＆リカバリ**: ADVANCED.md にセクション追加
  - 長期記憶の4層構造（Loop/Provisional/階層Digest/Essence）
  - 再構築可能性に基づくバックアップ優先度（Loopのみ必須）
  - Git連携/手動/クラウド同期の3つの方法
  - リカバリ手順（各層別）と推奨頻度

### Changed
- **SSoT参照の徹底**:
  - `digest-auto/SKILL.md`: 「まだらボケ」説明をREADME.md SSoT参照に簡略化
  - `FAQ.md`: 「まだらボケ」回答をSSoT参照に簡略化
- **バージョン情報統一**:
  - `ARCHITECTURE.md`, `TROUBLESHOOTING.md`, `API_REFERENCE.md` にバージョンヘッダー追加
- **ドキュメント改善**:
  - ドキュメント健全性診断に基づく改善
  - 重複コンテンツ削減
  - ADVANCED.md 目次更新

---

## [1.1.7] - 2025-11-27

### Changed
- **ドキュメントリファクタリング**: 大規模なドキュメント整理
  - README.md: トラフィックディレクター化（大幅簡略化）
  - docs/README.md: AI Specification Hub に特化
  - バージョンフッター削除 - SSoTに集約
  - ブレッドクラム追加（docs/配下）
  - scripts/README.md: shadow/, finalize/, __version__.py を追記

### Fixed
- **パス参照修正**: `homunculus/Toybox` → プレースホルダーに変更
  - `skills/digest-config/SKILL.md` (line 26, 97)
  - `skills/digest-setup/SKILL.md` (line 27)
- **ドキュメント整備**:
  - ARCHITECTURE.md: カスケードフローのSSoT参照を追加
  - 全docsファイルにブレッドクラムナビゲーション追加
  - ペルソナベースのナビゲーションテーブル導入

---

## [1.1.6] - 2025-11-27

### Added
- **shadow/ パッケージ**: `shadow_grand_digest.py` を4つのモジュールに分割
  - `shadow/template.py`: テンプレート生成（ShadowTemplate クラス）
  - `shadow/file_detector.py`: ファイル検出（FileDetector クラス）
  - `shadow/shadow_io.py`: Shadow I/O（ShadowIO クラス）
  - `shadow/shadow_updater.py`: Shadow更新（ShadowUpdater クラス）

### Changed
- **リファクタリング**: shadow_grand_digest.py のFacade分割
  - 元ファイルはFacadeとして後方互換性を維持

---

## [1.1.5] - 2025-11-27

### Added
- **finalize/ パッケージ**: `finalize_from_shadow.py` を4つのモジュールに分割
  - `finalize/shadow_validator.py`: Shadow検証（ShadowValidator クラス）
  - `finalize/provisional_loader.py`: Provisional読込（ProvisionalLoader クラス）
  - `finalize/digest_builder.py`: Digest構築（RegularDigestBuilder クラス）
  - `finalize/persistence.py`: 永続化処理（DigestPersistence クラス）

### Changed
- **リファクタリング**: finalize_from_shadow.py のFacade分割
  - 元ファイルはFacadeとして後方互換性を維持

---

## [1.1.4] - 2025-11-27

### Changed
- **リファクタリング**: 例外処理の完全移行
  - `exceptions.py` の例外クラス（`ValidationError`, `DigestError`, `FileIOError`）を実際に使用開始
  - `log_error()` → 適切な例外に置換
  - 各メソッドの戻り値を `bool`/`Optional` から例外ベースに変更
  - 関連テストを `assertFalse()` → `assertRaises()` に更新

---

## [1.1.3] - 2025-11-27

### Added
- **__version__.py**: バージョン定数のSingle Source of Truth（`DIGEST_FORMAT_VERSION`）を新規作成

### Changed
- **リファクタリング**: バージョン文字列の集約
  - ハードコードされていた `"1.0"` を `DIGEST_FORMAT_VERSION` 定数に置換
- **リファクタリング**: validators.py の段階的採用
  - `isinstance()` → `is_valid_dict()`/`is_valid_list()` に置換

---

## [1.1.2] - 2025-11-27

### Fixed
- **plugin.json**: バージョン番号を 1.1.2 に更新（CHANGELOGとの整合性確保）
- **digest-auto/SKILL.md**: パス参照を修正（Toybox → Weave）
- **save_provisional_digest.py**: Provisional Digestのフィールド名を `source_file` に統一（digest_types.pyとの整合性確保）
- **ARCHITECTURE.md**: Provisional Digestのフィールド名を `source_file` に統一

### Changed
- **SKILL.md**: 実装ガイドラインを共通ファイル（_implementation-notes.md）への参照に変更（重複削減）

---

## [1.1.1] - 2025-11-27

### Changed
- **ARCHITECTURE.md**: GrandDigest/ShadowGrandDigest/Provisionalのファイル形式をソースコードに合わせて修正
- **API_REFERENCE.md**: format_digest_number(), PLACEHOLDER_*定数, utils.py関数群を追記
- **TROUBLESHOOTING.md**: Provisionalパス修正、last_digest_times.jsonパス修正
- **GUIDE.md**: SSoT参照化によりまだらボケ説明を簡略化、トラブルシューティングをTROUBLESHOOTING.md参照に変更
- **GLOSSARY.md**: SSoT参照化
- **FAQ.md**: SSoT参照化
- **docs/README.md**: SSoTクロスリファレンス表を追加
- **skills/digest-setup/SKILL.md**: Provisionalディレクトリパス修正

### Fixed
- 全ドキュメントの日付を2025-11-27に統一
- ドキュメント間の重複記載を削減（Single Source of Truth確立）

---

## [1.1.0] - 2025-11-26

### Added
- **GLOSSARY.md**: 用語集を新規作成
- **QUICKSTART.md**: 5分クイックスタートガイドを新規作成
- **docs/README.md**: ドキュメントハブを新規作成
- **skills/shared/**: 共通コンポーネントディレクトリを新規作成
  - `_common-concepts.md`: まだらボケ、記憶定着サイクルの共通定義
  - `_implementation-notes.md`: 実装ガイドラインの共通定義
- **CHANGELOG.md**: 変更履歴ファイルを新規作成

### Changed
- **ARCHITECTURE.md**: バージョン表記を1.3.0から1.1.0に修正（整合性確保）
- **README.md**: プラグインパスを`@Plugins-Weave`に統一
- **TROUBLESHOOTING.md**: ファイル命名規則の説明を修正
- **digest-setup/SKILL.md**: サンプルパスを変数形式に変更
- **digest-config/SKILL.md**: サンプルパスを変数形式に変更
- **digest-auto/SKILL.md**: サンプルパスを変数形式に変更

### Fixed
- ドキュメント間のバージョン不整合を解消
- プラグイン名（@Toybox → @Plugins-Weave）の統一
- ファイル命名規則の説明を正確な形式に修正

---

## [1.0.0] - 2025-11-24

### Added
- 初回リリース
- 8階層の記憶構造（Weekly〜Centurial）
- `/digest` コマンド
- `@digest-setup` スキル
- `@digest-config` スキル
- `@digest-auto` スキル
- DigestAnalyzerエージェント
- GrandDigest/ShadowGrandDigest管理
- Provisional/Regular Digest生成
- まだらボケ検出機能

</details>

---

## バージョニング規則

- **MAJOR**: 互換性のない変更
- **MINOR**: 後方互換性のある機能追加
- **PATCH**: 後方互換性のあるバグ修正

---
**EpisodicRAG** by Weave | [GitHub](https://github.com/Bizuayeu/Plugins-Weave)
