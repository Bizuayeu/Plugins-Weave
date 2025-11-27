# Scripts

内部スクリプト（開発者向け）

---

## Overview

このディレクトリには、EpisodicRAGプラグインのPython実装が含まれています。

**通常のユーザーはこれらのスクリプトを直接実行する必要はありません。**

---

## Architecture (Clean Architecture)

v2.0.0 より、Clean Architecture（4層構造）を採用しています。

```
scripts/
├── domain/           # コアビジネスロジック（最内層）
├── infrastructure/   # 外部関心事
├── application/      # ユースケース
├── interfaces/       # エントリーポイント
├── config.py         # 設定管理クラス
└── test/             # テスト（301テスト）
```

### 依存関係ルール

```
domain/           ← 何にも依存しない
    ↑
infrastructure/   ← domain/ のみ
    ↑
application/      ← domain/ + infrastructure/
    ↑
interfaces/       ← application/
```

---

## Layers

### domain/ - コアビジネスロジック（最内層）

外部に依存しない純粋なビジネスロジック。

| Module | Purpose |
|--------|---------|
| `version.py` | バージョン定数（`__version__`, `DIGEST_FORMAT_VERSION`） |
| `constants.py` | `LEVEL_CONFIG`, `PLACEHOLDER_*`, `DEFAULT_THRESHOLDS` |
| `exceptions.py` | カスタム例外（`EpisodicRAGError`, `ValidationError`, etc.） |
| `types.py` | TypedDict定義（`BaseMetadata`, `DigestMetadata`, etc.） |
| `file_naming.py` | ファイル命名ユーティリティ（`extract_file_number()`, `format_digest_number()`） |

```python
from domain import LEVEL_CONFIG, __version__, ValidationError
from domain.file_naming import extract_file_number, format_digest_number
```

### infrastructure/ - 外部関心事

ファイルI/O、ロギングなどの外部関心事。

| Module | Purpose |
|--------|---------|
| `json_repository.py` | JSON読み書き（`load_json`, `save_json`, `load_json_with_template`） |
| `file_scanner.py` | ファイルスキャン（`scan_files`, `get_max_numbered_file`） |
| `logging_config.py` | ロギング設定（`log_info`, `log_warning`, `log_error`） |

```python
from infrastructure import load_json, save_json, log_info, log_error
from infrastructure.file_scanner import scan_files, get_max_numbered_file
```

### application/ - ユースケース

ビジネスロジックの実装。

| Package | Purpose |
|---------|---------|
| `validators.py` | バリデーション関数（`validate_dict`, `is_valid_list`） |
| `tracking/` | 時間追跡（`DigestTimesTracker`） |
| `shadow/` | Shadow管理（`ShadowTemplate`, `ShadowUpdater`, `ShadowIO`, `FileDetector`） |
| `grand/` | GrandDigest管理（`GrandDigestManager`, `ShadowGrandDigestManager`） |
| `finalize/` | Finalize処理（`ShadowValidator`, `ProvisionalLoader`, `RegularDigestBuilder`, `DigestPersistence`） |

```python
from application.shadow import ShadowTemplate, ShadowUpdater
from application.grand import GrandDigestManager, ShadowGrandDigestManager
from application.finalize import RegularDigestBuilder, DigestPersistence
from application.validators import validate_dict, is_valid_list
```

### interfaces/ - エントリーポイント

外部からのエントリーポイント。

| Module | Class | Purpose |
|--------|-------|---------|
| `finalize_from_shadow.py` | `DigestFinalizerFromShadow` | メインエントリーポイント |
| `save_provisional_digest.py` | `ProvisionalDigestSaver` | Provisional保存 |
| `interface_helpers.py` | - | ヘルパー関数（`sanitize_filename`, `get_next_digest_number`） |

```python
from interfaces import DigestFinalizerFromShadow, ProvisionalDigestSaver
from interfaces.interface_helpers import sanitize_filename, get_next_digest_number
```

### config.py - 設定管理

`DigestConfig` クラスを提供。Plugin自己完結版の設定管理。

```python
from config import DigestConfig

config = DigestConfig()
print(config.loops_path)
print(config.get_threshold("weekly"))
```

---

## Shell Scripts

| Script | Purpose |
|--------|---------|
| `setup.sh` | 開発環境セットアップ |
| `generate_digest_auto.sh` | 自動Digest生成 |

---

## Tests

`test/` ディレクトリにユニットテストがあります（**301テスト**）。

```bash
# 全テスト実行
cd scripts
python -m pytest test/ -v

# 特定テストファイル実行
python -m pytest test/test_validators.py -v

# 層別インポート確認
python -c "from domain import LEVEL_CONFIG, __version__; print(__version__)"
python -c "from infrastructure import load_json, log_info; print('OK')"
python -c "from application import ShadowGrandDigestManager; print('OK')"
python -c "from interfaces import DigestFinalizerFromShadow; print('OK')"
```

---

## See Also

- [ARCHITECTURE.md](../docs/ARCHITECTURE.md) - 技術仕様
- [API_REFERENCE.md](../docs/API_REFERENCE.md) - API リファレンス
- [CONTRIBUTING.md](../CONTRIBUTING.md) - 開発参加ガイド
- [HANDOFF.md](../HANDOFF.md) - リファクタリング引継ぎドキュメント

---
