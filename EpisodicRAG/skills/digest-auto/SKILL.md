---
name: digest-auto
description: EpisodicRAG 健全性診断と階層推奨
---

# digest-auto - 健全性診断と階層推奨スキル

EpisodicRAG システムの現在の状態を分析することで、
まだらボケ（未処理 Loop/プレースホルダー/欠番）を検出し、
生成可能なダイジェスト階層を判別するスキルです。
まだらボケの早期検出・予防のため、定期的に実行することを推奨します。

## 目次

- [用語説明](#用語説明)
- [実装時の注意事項](#実装時の注意事項)
- [まだらボケとは](#まだらボケとは)
- [実行フロー](#実行フロー)
- [分析フロー（CLI内部）](#分析フローcli内部)
- [出力例](#出力例)

---

## 用語説明

> 📖 パス用語（plugin_root / base_dir / paths）・ID桁数・命名規則は [用語集](../../GLOSSARY.md#基本概念) を参照

---

## 実装時の注意事項

> **UIメッセージ出力時は必ずコードブロックで囲むこと！**
> VSCode拡張では単一改行が空白に変換されるため、
> 対話型メッセージは三連バッククォートで囲む必要があります。

> 📖 共通の実装ガイドライン（パス検証、閾値検証、バリデーション、エラーハンドリング）は [_implementation-notes.md](../shared/_implementation-notes.md) を参照してください。

---

## まだらボケとは

> 📖 まだらボケの定義・発生パターン・記憶定着サイクル・対策は [用語集](../../GLOSSARY.md#まだらボケ) を参照

---

## 実行フロー

**⚠️ 重要: 以下のTodoリストをTodoWriteで作成し、順番に実行すること**

```
TodoWrite items:
1. システム状態取得 - digest_auto.pyを実行
2. 結果解釈 - JSONを解析して問題を特定
3. ユーザー報告 - テキストで状態を報告
4. 推奨アクション提示 - /digestや/digest {level}を推奨
```

| Step | 実行内容 | 使用スクリプト/処理 |
|------|---------|-------------------|
| 1 | システム状態取得 | `python -m interfaces.digest_auto --output json` |
| 2 | 結果解釈 | Claude が JSON を解析 |
| 3 | ユーザー報告 | Claude がテキストで報告 |
| 4 | 推奨アクション提示 | `/digest` や `/digest {level}` を推奨 |

**配置先**: `scripts/interfaces/digest_auto.py`

---

## 分析フロー（CLI内部）

### 概要

Step 1 の CLI 実行時、以下の全ステップがCLI内部で処理されます。

| Step | 実行内容 |
|------|---------|
| 1 | 設定ファイル読み込み（DigestConfig から取得） |
| 2 | 未処理 Loop 検出（まだらボケ予防） |
| 3 | ShadowGrandDigest 確認（未確定ファイル数） |
| 4 | 中間ファイルスキップ検出（欠番検出） |
| 5 | GrandDigest 確認（各階層の確定済みファイル数） |
| 6 | 生成可能な階層判定（閾値との比較） |
| 7 | プレースホルダー検出（まだらボケケース2） |
| 8 | 推奨アクション提示（生成可能な階層と不足ファイル数） |

### エラー発生時の動作

| Step | エラー内容 | 推奨アクション |
|------|-----------|---------------|
| 1 | 初期セットアップ未完了 | `@digest-setup` を実行 |
| 2 | 未処理Loop検出 | `/digest` を実行（即終了） |
| 3 | ShadowGrandDigest未作成 | `@digest-setup` を実行 |
| 7 | プレースホルダー検出 | `/digest` を実行（即終了） |

---

## 出力例

`status` は `error` / `warning` / `ok` の 3 値。以下は各 1 例で、実際の構造は CLI 出力を
そのまま読む。

### error（即終了）


```json
{
  "status": "error",
  "error": "Config file not found",
  "action": "Run @digest-setup"
}
```

### warning（処理継続）


```json
{
  "status": "warning",
  "issues": [
    {"type": "unprocessed_loops", "count": 1, "files": ["L00001"]}
  ],
  "recommendations": ["Run /digest to process unprocessed loops"]
}
```

### ok（推奨アクション）


```json
{
  "status": "ok",
  "issues": [],
  "generatable_levels": [
    {"level": "weekly", "current": 7, "threshold": 5, "ready": true}
  ],
  "recommendations": ["Run /digest weekly to generate Weekly Digest"]
}
```

### テキスト出力（--output text）

```bash
python -m interfaces.digest_auto --output text
```

```text
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 EpisodicRAG システム状態
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✅ 生成可能なダイジェスト

  ✅ Weekly (7/5 Loops)
     → `/digest weekly` で生成できます！

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---
**EpisodicRAG** by Weave | [GitHub](https://github.com/Bizuayeu/Plugins-Weave)
