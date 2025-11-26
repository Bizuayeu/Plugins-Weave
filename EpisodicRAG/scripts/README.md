# Scripts

内部スクリプト（開発者向け）

---

## Overview

このディレクトリには、プラグインの内部処理に使用するPython/Bashスクリプトが含まれています。

**通常のユーザーはこれらのスクリプトを直接実行する必要はありません。**

---

## Core Modules

| Module | Purpose |
|--------|---------|
| `config.py` | 設定管理・パス解決 |
| `shadow_grand_digest.py` | ShadowGrandDigest管理 |
| `finalize_from_shadow.py` | Digest確定処理 |
| `grand_digest.py` | GrandDigest.txt CRUD操作 |
| `digest_times.py` | last_digest_times.json管理 |
| `save_provisional_digest.py` | Provisional Digest保存 |

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

`test/` ディレクトリにユニットテストがあります。

```bash
# 全テスト実行
python -m pytest test/ -v

# 個別実行
python test/test_config.py
```

---

## See Also

- [ARCHITECTURE.md](../docs/ARCHITECTURE.md) - 技術仕様
- [CONTRIBUTING.md](../CONTRIBUTING.md) - 開発参加ガイド

---

*Last Updated: 2025-11-27*
*Version: 1.1.2*
