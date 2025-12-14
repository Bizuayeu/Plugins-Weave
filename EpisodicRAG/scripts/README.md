# Scripts

EpisodicRAGプラグインのPython実装リファレンス

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture-clean-architecture)
- [Layers](#layers)
- [Shell Scripts](#shell-scripts)
- [Tests](#tests)
- [See Also](#see-also)

---

## Overview

| 対象 | 用途 |
|------|------|
| **ユーザー** | CLIコマンド（`python -m interfaces.digest_*`）またはスキル経由で使用 |
| **開発者** | 各層のモジュールを直接インポートして拡張 |

> 📖 使い方: [QUICKSTART.md](../docs/user/QUICKSTART.md) / 技術仕様: [ARCHITECTURE.md](../docs/dev/ARCHITECTURE.md)

---

## Architecture (Clean Architecture)

v2.0.0 より、Clean Architecture（4層構造）を採用しています。

> 📖 **詳細仕様**（層構造・依存関係ルール・推奨インポートパス）: [ARCHITECTURE.md](../docs/dev/ARCHITECTURE.md#clean-architecture)

```text
scripts/
├── domain/           # コアビジネスロジック（最内層）
│   └── config/       # 設定定数・バリデーション
├── infrastructure/   # 外部関心事（I/O、ロギング）
│   └── config/       # 設定ファイルI/O・パス解決
├── application/      # ユースケース
│   └── config/       # DigestConfig（Facade）
├── interfaces/       # エントリーポイント
├── tools/            # 開発ツール
│   ├── check_footer.py    # フッターチェック
│   ├── link_checker.py    # リンク検証
│   └── validate_json.py   # JSON検証
└── test/             # テスト
```

### 依存関係ルール

```text
domain/           ← 何にも依存しない（純粋なビジネスロジック）
    ↑
infrastructure/   ← domain/ のみ
    ↑
application/      ← domain/ + infrastructure/
    ↑
interfaces/       ← application/
```

> **Note**: v4.0.0より、設定管理機能（config）は各層のサブディレクトリに分散配置されています。
> 詳細: [ARCHITECTURE.md](../docs/dev/ARCHITECTURE.md#clean-architecture)

---

## Layers

### domain/ - 定数・型・例外

| Module | Purpose |
|--------|---------|
| `version.py` | バージョン定数（`__version__`, `DIGEST_FORMAT_VERSION`） |
| `constants.py` | `LEVEL_CONFIG`, `PLACEHOLDER_*`, `DEFAULT_THRESHOLDS` |
| `exceptions.py` | カスタム例外（`EpisodicRAGError`, `ValidationError`, etc.） |
| `protocols.py` | Protocol定義（型ヒント用インターフェース） |
| `types/` | TypedDict定義パッケージ（`BaseMetadata`, `DigestMetadata`, Literal型等）*(v4.1.0+パッケージ化)* |
| `validators/` | バリデーションパッケージ（`digest_validators`, `runtime_checks`, `helpers`, `type_validators`） |
| `file_naming.py` | ファイル命名ユーティリティ（`extract_file_number()`, `format_digest_number()`） |
| `file_constants.py` | ファイル関連定数 |
| `validation.py` | バリデーションロジック |
| `validation_helpers.py` | バリデーションヘルパー関数 |
| `text_utils.py` | テキスト処理ユーティリティ |
| `level_metadata.py` | レベルメタデータ定義 |
| `level_behaviors.py` | レベル固有振る舞い定義 |
| `level_registry.py` | レベル固有振る舞いのRegistry（Strategy Pattern） |
| `error_formatter/` | エラーメッセージの標準化パッケージ（`CompositeErrorFormatter`, `FormatterRegistry`）|

```python
from domain import LEVEL_CONFIG, __version__, ValidationError
from domain.file_naming import extract_file_number, format_digest_number
from domain.level_registry import get_level_registry
from domain.validators import digest_validators, runtime_checks
```

### infrastructure/ - 外部I/O

| Module | Purpose |
|--------|---------|
| `json_repository/` | JSON操作パッケージ（`load_json`, `save_json`, `ChainedLoader`）|
| `file_scanner.py` | ファイルスキャン（`scan_files`, `get_max_numbered_file`） |
| `logging_config.py` | ロギング設定（`log_info`, `log_warning`, `log_error`） |
| `structured_logging.py` | 構造化ロギング |
| `error_handling.py` | エラーハンドリングユーティリティ |
| `user_interaction.py` | ユーザー確認プロンプト（`get_default_confirm_callback`） |

```python
from infrastructure import load_json, save_json, log_info, log_error
from infrastructure.file_scanner import scan_files, get_max_numbered_file
from infrastructure.user_interaction import get_default_confirm_callback
from infrastructure.error_handling import handle_error
```

### application/ - ビジネスロジック

| Package | Purpose |
|---------|---------|
| `validators.py` | バリデーション関数（`validate_dict`, `is_valid_list`） |
| `tracking/` | 時間追跡（`DigestTimesTracker`） |
| `shadow/` | Shadow管理（`ShadowTemplate`, `ShadowUpdater`, `ShadowIO`, `FileDetector`, `CascadeProcessor`, `CascadeOrchestrator` *(v4.1.0+)*, `FileAppender`, `PlaceholderManager`, `ProvisionalAppender`） |
| `grand/` | GrandDigest管理（`GrandDigestManager`, `ShadowGrandDigestManager`） |
| `finalize/` | Finalize処理（`ShadowValidator`, `ProvisionalLoader`, `RegularDigestBuilder`, `DigestPersistence`） |

```python
from application.shadow import ShadowTemplate, ShadowUpdater
from application.grand import GrandDigestManager, ShadowGrandDigestManager
from application.finalize import RegularDigestBuilder, DigestPersistence
from domain.validators import validate_type, is_valid_dict, is_valid_list
```

### interfaces/ - エントリーポイント

| Module | Class | Purpose |
|--------|-------|---------|
| `finalize_from_shadow.py` | `DigestFinalizerFromShadow` | メインエントリーポイント |
| `save_provisional_digest.py` | `ProvisionalDigestSaver` | Provisional保存 |
| `digest_setup.py` | - | 初期セットアップCLI (`python -m interfaces.digest_setup`) |
| `digest_config.py` | - | 設定変更CLI (`python -m interfaces.digest_config`) |
| `digest_auto.py` | - | 健全性診断CLI (`python -m interfaces.digest_auto`) |
| `shadow_state_checker.py` | - | Shadow状態チェッカー |
| `config_cli.py` | - | 設定CLIエントリーポイント |
| `interface_helpers.py` | - | ヘルパー関数（`sanitize_filename`, `get_next_digest_number`） |
| `cli_helpers.py` | - | CLI共通ヘルパー（`output_json`, `output_error`）*(v4.1.0+)* |
| `find_plugin_root.py` | - | プラグインルート検出 |
| `digest_entry.py` | - | Digestエントリーポイント |
| `digest_readiness.py` | - | Digest準備状態チェック |
| `update_digest_times.py` | - | Digestタイムスタンプ更新 |
| `provisional/` | - | Provisionalマージ処理（`file_manager`, `input_loader`, `merger`, `validator`） |

```python
from interfaces import DigestFinalizerFromShadow, ProvisionalDigestSaver
from interfaces.interface_helpers import sanitize_filename, get_next_digest_number
from interfaces.provisional import ProvisionalMerger
```

### 設定管理（各層のconfig/）

v4.0.0より、設定管理機能は各層のサブディレクトリに分散配置されています。

| 層 | Package | Purpose |
|---|---------|---------|
| **domain** | `domain/config/` | 設定定数（`REQUIRED_CONFIG_KEYS`, `THRESHOLD_KEYS`）、バリデーションヘルパー |
| **infrastructure** | `infrastructure/config/` | 設定ファイルI/O（`ConfigLoader`, `ConfigRepository`）、パス解決（`PathResolver`, `PluginRootResolver`） |
| **application** | `application/config/` | DigestConfig（Facade）、サービスクラス（`ConfigValidator`, `LevelPathService`, `ThresholdProvider`） |

```python
# アプリケーション層のFacade経由で使用（推奨）
from application.config import DigestConfig

config = DigestConfig()
print(config.loops_path)
print(config.get_threshold("weekly"))

# 層別に直接使用する場合
from domain.config import REQUIRED_CONFIG_KEYS
from infrastructure.config import ConfigLoader
from application.config import ThresholdProvider
```

---

## Shell Scripts

> **Note**: シェルスクリプトは廃止されました。Python CLI を使用してください。
>
> - セットアップ: `python -m interfaces.digest_setup`
> - Digest生成: `/digest` コマンド（commands/digest.md 参照）

---

## Tests

`test/` ディレクトリにユニットテストがあります。

> 📊 最新のテスト数は [CI バッジ](https://github.com/Bizuayeu/Plugins-Weave/actions) を参照してください。

### テストディレクトリ構造

```text
test/
├── conftest.py              # 共通フィクスチャ
├── test_constants.py        # 定数テスト
├── test_helpers.py          # ヘルパーテスト
├── TESTING.md               # テスト方針ドキュメント
├── domain_tests/            # domain層テスト
├── infrastructure_tests/    # infrastructure層テスト
├── application_tests/       # application層テスト
├── interfaces_tests/        # interfaces層テスト
├── config_tests/            # config層テスト（v4.0.0+）
├── cli_integration_tests/   # CLI統合テスト（v4.0.0+）
├── integration_tests/       # 統合テスト
├── performance_tests/       # パフォーマンステスト
└── tools_tests/             # 開発ツールテスト（v4.1.0+）
```

### テスト実行

```bash
# 全テスト実行
cd scripts
python -m pytest test/ -v

# 層別テスト実行
python -m pytest test/domain_tests/ -v
python -m pytest test/application_tests/ -v
python -m pytest test/integration_tests/ -v

# パフォーマンステスト
python -m pytest test/performance_tests/ -v

# 層別インポート確認
python -c "from domain import LEVEL_CONFIG, __version__; print(__version__)"
python -c "from infrastructure import load_json, log_info; print('OK')"
python -c "from application import ShadowGrandDigestManager; print('OK')"
python -c "from interfaces import DigestFinalizerFromShadow; print('OK')"
```

---

## See Also

- [ARCHITECTURE.md](../docs/dev/ARCHITECTURE.md) - 技術仕様
- [API_REFERENCE.md](../docs/dev/API_REFERENCE.md) - API リファレンス
- [DESIGN_DECISIONS.md](../docs/dev/DESIGN_DECISIONS.md) - 設計判断
- [LEARNING_PATH.md](../docs/dev/LEARNING_PATH.md) - Python学習パス
- [CONTRIBUTING.md](../CONTRIBUTING.md) - 開発参加ガイド

---
**EpisodicRAG** by Weave | [GitHub](https://github.com/Bizuayeu/Plugins-Weave)
