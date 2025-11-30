---
name: digest-config
description: EpisodicRAG設定変更（対話的）
---

# digest-config - 設定変更スキル

EpisodicRAG プラグインの設定を対話的に変更するスキルです。

## 目次

- [用語説明](#用語説明)
- [設定変更フロー](#設定変更フロー)
- [CLIスクリプト](#cliスクリプト)
- [スキルの自律判断](#スキルの自律判断)
- [使用例](#使用例)
- [実装時の注意事項](#重要実装時の注意事項)

## 用語説明

> 📖 パス用語（plugin_root / base_dir / paths）は [用語集](../../README.md#基本概念) を参照

## 設定変更フロー

### 概要

1. Claudeが `show` コマンドで現在の設定を取得
2. ユーザーに変更項目を質問
3. 変更内容を確認
4. `set` または `update` コマンドで設定を更新
5. 結果をユーザーに報告

---

## CLIスクリプト

### 配置先

```
scripts/interfaces/digest_config.py
```

### コマンド

#### 現在の設定を取得

```bash
python -m interfaces.digest_config show
```

**出力例:**
```json
{
  "status": "ok",
  "config": {
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
      ...
    }
  },
  "resolved_paths": {
    "plugin_root": "/path/to/plugin",
    "base_dir": "/path/to/plugin",
    "loops_path": "/path/to/plugin/data/Loops",
    "digests_path": "/path/to/plugin/data/Digests",
    "essences_path": "/path/to/plugin/data/Essences"
  }
}
```

#### 個別設定の更新

```bash
# 閾値の変更
python -m interfaces.digest_config set --key "levels.weekly_threshold" --value 7

# パスの変更
python -m interfaces.digest_config set --key "paths.loops_dir" --value "custom/Loops"

# base_dirの変更
python -m interfaces.digest_config set --key "base_dir" --value "~/DEV/data"
```

**出力例:**
```json
{
  "status": "ok",
  "message": "Updated levels.weekly_threshold",
  "old_value": 5,
  "new_value": 7
}
```

#### 設定を完全更新

```bash
python -m interfaces.digest_config update --config '{
  "base_dir": ".",
  "paths": {...},
  "levels": {...}
}'
```

#### trusted_external_paths の管理

```bash
# 一覧表示
python -m interfaces.digest_config trusted-paths list

# パスを追加
python -m interfaces.digest_config trusted-paths add "~/DEV/production"

# パスを削除
python -m interfaces.digest_config trusted-paths remove "~/DEV/production"
```

**出力例（list）:**
```json
{
  "status": "ok",
  "trusted_external_paths": ["~/DEV/production"],
  "count": 1
}
```

---

## スキルの自律判断

このスキルは**自律的には起動しません**。必ずユーザーの明示的な呼び出しが必要です。

理由：

- 設定変更はユーザーの意図を確認する必要がある
- 誤った設定変更を防ぐため
- 対話的な確認が必要

---

## 使用例

### 例 1: weekly threshold を変更

```text
@digest-config weekly threshold を 7 に変更
```

Claudeの動作:
1. `show` で現在の設定を確認
2. ユーザーに変更確認
3. `set --key "levels.weekly_threshold" --value 7` を実行

### 例 2: 外部データディレクトリを使用

```text
@digest-config 外部のデータディレクトリを使いたい
```

Claudeの動作:
1. `trusted-paths add "~/DEV/production"` でパスを許可
2. `set --key "base_dir" --value "~/DEV/production/EpisodicRAG"` で変更

### 例 3: 設定全体を確認

```text
@digest-config 設定を確認
```

Claudeの動作:
1. `show` を実行
2. 結果をユーザーに分かりやすく表示

---

## 【重要】実装時の注意事項

> 📖 共通の実装ガイドラインである（バリデーション、エラーハンドリング）は [_implementation-notes.md](../shared/_implementation-notes.md) を**必ず参照**してください。

---

**このスキルは、EpisodicRAG プラグインの設定を対話的に変更します ⚙️**

---
