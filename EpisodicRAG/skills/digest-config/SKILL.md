---
name: digest-config
description: EpisodicRAG設定変更（対話的）
---

# digest-config - 設定変更スキル

EpisodicRAG プラグインの設定を対話的に変更するスキルです。
このスキルは**自律的には起動しません**（ユーザーの明示的な呼び出しが必要）。

## 目次

- [用語説明](#用語説明)
- [実装時の注意事項](#実装時の注意事項)
- [実行フロー](#実行フロー)
- [使用例](#使用例)
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
1. 現在設定取得 - digest_config showを実行
2. 変更項目確認 - ユーザーに変更内容を質問
3. 変更内容確認 - 変更前後を表示してユーザーに確認
4. 設定更新 - digest_config setを実行
5. 結果報告 - 更新結果をユーザーに報告
```

| Step | 実行内容 | 使用スクリプト/処理 |
|------|---------|-------------------|
| 1 | 現在の設定取得 | `python -m interfaces.digest_config show` |
| 2 | 変更項目を質問 | Claude がユーザーに質問 |
| 3 | 変更内容確認 | Claude がユーザーに確認 |
| 4 | 設定更新 | `python -m interfaces.digest_config set --key "..." --value ...` |
| 5 | 結果報告 | Claude がユーザーに報告 |

**配置先**: `scripts/interfaces/digest_config.py`

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

## 出力例

### show（設定取得）

```json
{
  "status": "ok",
  "config": {
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
      ...
    }
  },
  "resolved_paths": {
    "plugin_root": "/path/to/plugin",
    "base_dir": "/home/user/.claude/plugins/.episodicrag",
    "loops_path": "/home/user/.claude/plugins/.episodicrag/data/Loops",
    "digests_path": "/home/user/.claude/plugins/.episodicrag/data/Digests",
    "essences_path": "/home/user/.claude/plugins/.episodicrag/data/Essences"
  }
}
```

### set（設定更新）

```json
{
  "status": "ok",
  "message": "Updated levels.weekly_threshold",
  "old_value": 5,
  "new_value": 7
}
```

### trusted-paths list

```json
{
  "status": "ok",
  "trusted_external_paths": ["~/DEV/production"],
  "count": 1
}
```

---
**EpisodicRAG** by Weave | [GitHub](https://github.com/Bizuayeu/Plugins-Weave)
