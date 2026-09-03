---
name: digest-setup
description: EpisodicRAG初期セットアップ（対話的）
---

# digest-setup - 初期セットアップスキル

EpisodicRAG プラグインの初期セットアップを対話的に実行するスキルです。
このスキルは**自律的には起動しません**（ユーザーの明示的な呼び出しが必要）。

## 目次

- [用語説明](#用語説明)
- [実装時の注意事項](#実装時の注意事項)
- [実行フロー](#実行フロー)
- [デフォルト設定例](#デフォルト設定例)
- [出力例](#出力例)
---

## 用語説明

> 📖 パス用語（plugin_root / base_dir / paths）・ID桁数・命名規則は [用語集](../../GLOSSARY.md#基本概念) を参照

---

## 実装時の注意事項

> **UI メッセージはコードブロックで囲む。**
> VSCode拡張では単一改行が空白に変換されるため、
> 対話型メッセージは三連バッククォートで囲む必要があります。

> 📖 共通の実装ガイドライン（パス検証、閾値検証、バリデーション、エラーハンドリング）は [_implementation-notes.md](../shared/_implementation-notes.md) を参照してください。

---

## 実行フロー

**⚠️ 重要: 以下のTodoリストをTodoWriteで作成し、順番に実行すること**

```
TodoWrite items:
1. セットアップ状態確認 - digest_setup checkを実行
2. 対話的Q&A - ユーザーにパス・Threshold等を質問
3. 設定値収集 - 回答をJSON形式に構築
4. セットアップ実行 - digest_setup initを実行
5. 結果報告 - 作成されたファイル・ディレクトリを報告
```

| Step | 実行内容 | 使用スクリプト/処理 |
|------|---------|-------------------|
| 1 | セットアップ状態確認 | `python -m interfaces.digest_setup check` |
| 2 | 対話的Q&A | Claude がユーザーに質問（下記参照） |
| 3 | 設定値収集・JSON構築 | Claude が回答を JSON に構築 |
| 4 | セットアップ実行 | `python -m interfaces.digest_setup init --config '{...}'` |
| 5 | 結果報告 | Claude がユーザーに報告 |

**配置先**: `scripts/interfaces/digest_setup.py`

### 対話的Q&A（Step 2）

Claude がユーザーに確認する項目：
- Q1: Loopファイル配置先
- Q2: Digestsファイル配置先
- Q3: Essencesファイル配置先
- Q4: 外部Identity.md
- Q5: Threshold設定

> 📖 `trusted_external_paths` の詳細は [用語集](../../GLOSSARY.md#trusted_external_paths) を参照

### CLI内部処理（Step 4）

`init` コマンド実行時に以下が自動処理されます：
- 設定ファイル作成
- ディレクトリ作成（8階層 + Provisional）
- 初期ファイル作成（テンプレートからコピー）

---

## デフォルト設定例

### 永続化ディレクトリ使用（デフォルト）

```json
{
  "base_dir": "~/.claude/plugins/.episodicrag",
  "trusted_external_paths": ["~/.claude/plugins/.episodicrag"],
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

### カスタムディレクトリ使用時

```json
{
  "base_dir": "~/DEV/my-project/EpisodicRAG",
  "trusted_external_paths": ["~/DEV/my-project"],
  "paths": {
    "loops_dir": "data/Loops",
    "digests_dir": "data/Digests",
    "essences_dir": "data/Essences",
    "identity_file_path": null
  },
  "levels": { ... }
}
```

---

## 出力例

### check（状態確認）

**未セットアップ:**
```json
{
  "status": "not_configured",
  "config_exists": false,
  "directories_exist": false,
  "message": "Initial setup required"
}
```

**セットアップ済み:**
```json
{
  "status": "configured",
  "config_exists": true,
  "directories_exist": true,
  "config_file": "~/.claude/plugins/.episodicrag/config.json",
  "message": "Setup already completed"
}
```

### init（セットアップ実行）

```json
{
  "status": "ok",
  "created": {
    "config_file": "~/.claude/plugins/.episodicrag/config.json",
    "directories": ["data/Loops", "data/Digests/1_Weekly", ...],
    "files": ["GrandDigest.txt", "ShadowGrandDigest.txt", "last_digest_times.json"]
  },
  "warnings": [],
  "external_paths_detected": []
}
```

---
**EpisodicRAG** by Weave | [GitHub](https://github.com/Bizuayeu/Plugins-Weave)
