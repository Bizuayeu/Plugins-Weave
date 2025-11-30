---
name: digest-setup
description: EpisodicRAG初期セットアップ（対話的）
---

# digest-setup - 初期セットアップスキル

EpisodicRAG プラグインの初期セットアップを対話的に実行するスキルです。

## 目次

- [用語説明](#用語説明)
- [セットアップフロー](#セットアップフロー)
- [CLIスクリプト](#cliスクリプト)
- [スキルの自律判断](#スキルの自律判断)
- [デフォルト設定例](#デフォルト設定例)
- [実装時の注意事項](#重要実装時の注意事項)

## 用語説明

> 📖 パス用語（plugin_root / base_dir / paths）は [用語集](../../README.md#基本概念) を参照

## セットアップフロー

### 概要

1. 既存設定ファイル確認（再設定確認）
2. 対話的Q&A（Claudeが実施）
   - Q1: Loopファイル配置先
   - Q2: Digestsファイル配置先
   - Q3: Essencesファイル配置先
   - Q4: 外部Identity.md
   - Q5: Threshold設定
3. 設定ファイル作成
4. ディレクトリ作成（8階層 + Provisional）
5. 初期ファイル作成（テンプレートからコピー）
6. 完了報告（外部パス警告含む）

---

## CLIスクリプト

### 配置先

```
scripts/interfaces/digest_setup.py
```

### コマンド

#### セットアップ状態確認

```bash
python -m interfaces.digest_setup check
```

**出力例（未セットアップ）:**
```json
{
  "status": "not_configured",
  "config_exists": false,
  "directories_exist": false,
  "message": "Initial setup required"
}
```

**出力例（セットアップ済み）:**
```json
{
  "status": "configured",
  "config_exists": true,
  "directories_exist": true,
  "config_file": "/path/to/config.json",
  "message": "Setup already completed"
}
```

#### セットアップ実行

```bash
python -m interfaces.digest_setup init --config '{
  "base_dir": ".",
  "paths": {
    "loops_dir": "data/Loops",
    "digests_dir": "data/Digests",
    "essences_dir": "data/Essences",
    "identity_file_path": null
  },
  "levels": {
    "weekly_threshold": 5,
    "monthly_threshold": 5,
    "quarterly_threshold": 3,
    "annual_threshold": 4,
    "triennial_threshold": 3,
    "decadal_threshold": 3,
    "multi_decadal_threshold": 3,
    "centurial_threshold": 4
  }
}'
```

**出力例（成功）:**
```json
{
  "status": "ok",
  "created": {
    "config_file": "/path/to/config.json",
    "directories": ["data/Loops", "data/Digests/1_Weekly", ...],
    "files": ["GrandDigest.txt", "ShadowGrandDigest.txt", "last_digest_times.json"]
  },
  "warnings": [],
  "external_paths_detected": []
}
```

#### 強制再セットアップ

```bash
python -m interfaces.digest_setup init --config '...' --force
```

### Claudeによる対話フロー

1. Claudeは `check` コマンドでセットアップ状態を確認
2. ユーザーに対話的に設定値を質問
3. 収集した設定を JSON に構築
4. `init` コマンドでセットアップを実行
5. 結果をユーザーに報告

---

## スキルの自律判断

このスキルは**自律的には起動しません**。必ずユーザーの明示的な呼び出しが必要です。

理由：

- 初期設定は一度だけ実行すれば良い
- 設定の上書きは慎重に行うべき
- ユーザーの意図を確認する必要がある

---

## デフォルト設定例

### 完全自己完結型（デフォルト）

```json
{
  "base_dir": ".",
  "trusted_external_paths": [],
  "paths": {
    "loops_dir": "data/Loops",
    "digests_dir": "data/Digests",
    "essences_dir": "data/Essences",
    "identity_file_path": null
  },
  "levels": {
    "weekly_threshold": 5,
    "monthly_threshold": 5,
    "quarterly_threshold": 3,
    "annual_threshold": 4,
    "triennial_threshold": 3,
    "decadal_threshold": 3,
    "multi_decadal_threshold": 3,
    "centurial_threshold": 4
  }
}
```

### 外部ディレクトリ使用時

```json
{
  "base_dir": "~/DEV/production/EpisodicRAG",
  "trusted_external_paths": ["~/DEV/production"],
  "paths": {
    "loops_dir": "data/Loops",
    "digests_dir": "data/Digests",
    "essences_dir": "data/Essences",
    "identity_file_path": null
  },
  "levels": { ... }
}
```

> 📖 `trusted_external_paths` の詳細は [用語集](../../README.md#trusted_external_paths) を参照

---

## 【重要】実装時の注意事項

> 📖 共通の実装ガイドライン（パス検証、閾値検証、エラーハンドリング）である [_implementation-notes.md](../shared/_implementation-notes.md) を**必ず参照**してください。

---

**このスキルは、EpisodicRAG プラグインの初期セットアップを対話的に実行します 🛠️**

---
