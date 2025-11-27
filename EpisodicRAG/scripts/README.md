# Scripts

内部スクリプト（開発者向け）

---

## Overview

このディレクトリには、プラグインの内部処理に使用するPython/Bashスクリプトが含まれています。

**通常のユーザーはこれらのスクリプトを直接実行する必要はありません。**

---

## Version Management

| File | Purpose |
|------|---------|
| `__version__.py` | バージョン定数（SSoT） |

```python
from __version__ import __version__, DIGEST_FORMAT_VERSION
```

---

## Core Modules

| Module | Purpose |
|--------|---------|
| `config.py` | 設定管理・パス解決 |
| `shadow_grand_digest.py` | ShadowGrandDigest管理（Facade） |
| `finalize_from_shadow.py` | Digest確定処理（Facade） |
| `grand_digest.py` | GrandDigest.txt CRUD操作 |
| `digest_times.py` | last_digest_times.json管理 |
| `save_provisional_digest.py` | Provisional Digest保存 |

---

## Packages (v1.1.5+)

### shadow/ Package

ShadowGrandDigest管理の内部モジュール群（`shadow_grand_digest.py` のFacade実装）

| Module | Class | Purpose |
|--------|-------|---------|
| `template.py` | ShadowTemplate | テンプレート生成 |
| `file_detector.py` | FileDetector | ファイル検出 |
| `shadow_io.py` | ShadowIO | I/O操作 |
| `shadow_updater.py` | ShadowUpdater | Shadow更新 |

### finalize/ Package

Digest確定処理の内部モジュール群（`finalize_from_shadow.py` のFacade実装）

| Module | Class | Purpose |
|--------|-------|---------|
| `shadow_validator.py` | ShadowValidator | Shadow検証 |
| `provisional_loader.py` | ProvisionalLoader | Provisional読込 |
| `digest_builder.py` | RegularDigestBuilder | Digest構築 |
| `persistence.py` | DigestPersistence | 永続化処理 |

> **Note**: これらのパッケージは内部実装です。外部からは `shadow_grand_digest.py` / `finalize_from_shadow.py` のFacadeインターフェースを使用してください。

---

## Utility Modules

| Module | Purpose |
|--------|---------|
| `utils.py` | ユーティリティ関数 |
| `validators.py` | バリデーション |
| `exceptions.py` | カスタム例外 |
| `digest_types.py` | 型定義 |

---

## Shell Scripts

| Script | Purpose |
|--------|---------|
| `setup.sh` | 開発環境セットアップ |
| `generate_digest_auto.sh` | 自動Digest生成 |

---

## Tests

`test/` ディレクトリにユニットテストがあります（129テスト）。

```bash
# 全テスト実行
python -m pytest test/ -v

# 個別実行
python test/test_config.py
```

---

## See Also

- [ARCHITECTURE.md](../docs/ARCHITECTURE.md) - 技術仕様
- [API_REFERENCE.md](../docs/API_REFERENCE.md) - API リファレンス
- [CONTRIBUTING.md](../CONTRIBUTING.md) - 開発参加ガイド

---
