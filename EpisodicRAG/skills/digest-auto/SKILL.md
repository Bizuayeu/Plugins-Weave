---
name: digest-auto
description: EpisodicRAG 健全性診断と階層推奨
---

# digest-auto - 健全性診断と階層推奨スキル

EpisodicRAG システムの現在の状態を分析することで、
まだらボケ（未処理 Loop/プレースホルダー/欠番）を検出し、
生成可能なダイジェスト階層を推奨するスキルです。

## 目次

- [用語説明](#用語説明)
- [まだらボケとは](#まだらボケとは)
- [分析フロー](#分析フロー)
- [CLIスクリプト](#cliスクリプト)
- [スキルの自律判断](#スキルの自律判断)
- [出力例](#出力例)
- [実装時の注意事項](#重要実装時の注意事項)

## 用語説明

> 📖 パス用語・ID桁数・命名規則は [用語集](../../README.md) を参照

## まだらボケとは

> 📖 まだらボケの定義・発生パターン・記憶定着サイクル・対策は [用語集](../../README.md#まだらボケ) を参照

---

## 分析フロー

### 概要

1. **設定ファイル読み込み** - DigestConfig から設定を取得
2. **未処理 Loop 検出** - 最優先チェック（まだらボケ予防）
3. **ShadowGrandDigest 確認** - 未確定ファイル数を確認
4. **中間ファイルスキップ検出** - 欠番を検出
5. **GrandDigest 確認** - 各階層の確定済みファイル数を確認
6. **生成可能な階層判定** - 閾値との比較
7. **プレースホルダー検出** - まだらボケケース2
8. **推奨アクション提示** - 生成可能な階層と不足ファイル数を表示

### エラー発生時の動作

- **ステップ1でエラー**: 初期セットアップ未完了 → `@digest-setup` を推奨
- **ステップ2でエラー**: 未処理Loop検出 → `/digest` を推奨（即終了）
- **ステップ3でエラー**: ShadowGrandDigest未作成 → `@digest-setup` を推奨
- **ステップ7でエラー**: プレースホルダー検出 → `/digest` を推奨（即終了）

---

## CLIスクリプト

### 配置先

```
scripts/interfaces/digest_auto.py
```

### コマンド

#### 健全性診断（JSON出力）

```bash
python -m interfaces.digest_auto --output json
```

**出力例:**
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

#### 健全性診断（テキスト出力）

```bash
python -m interfaces.digest_auto --output text
```

**出力例:**
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

## スキルの自律判断

このスキルは**起動時に自動実行を推奨**します。

理由：

- まだらボケの早期検出・予防
- 生成可能な階層の把握
- システム状態の定期確認

Claudeの動作:

1. `--output json` でシステム状態を取得
2. 結果を解釈し、ユーザーに分かりやすく報告
3. 必要に応じて `/digest` や `/digest {level}` を推奨

---

## 出力例

### エラー系（即終了）

#### 例 1: 初期セットアップ未完了

```json
{
  "status": "error",
  "error": "Config file not found",
  "action": "Run @digest-setup"
}
```

#### 例 2: ShadowGrandDigest 未作成

```json
{
  "status": "error",
  "error": "ShadowGrandDigest.txt not found",
  "action": "Run @digest-setup"
}
```

#### 例 3: 未処理 Loop 検出（まだらボケ予防）

```json
{
  "status": "warning",
  "issues": [
    {"type": "unprocessed_loops", "count": 1, "files": ["L00001"]}
  ],
  "recommendations": ["Run /digest to process unprocessed loops"]
}
```

#### 例 4: プレースホルダー検出（まだらボケ）

```json
{
  "status": "warning",
  "issues": [
    {"type": "placeholders", "level": "weekly", "count": 3, "files": ["L00196", "L00197", "L00198"]}
  ],
  "recommendations": ["Run /digest to complete analysis"]
}
```

### 警告系（処理継続）

#### 例 5: 中間ファイルスキップ検出

```json
{
  "status": "warning",
  "issues": [
    {"type": "gaps", "level": "weekly", "range": "L00006-L00009", "missing": [7]}
  ],
  "recommendations": ["Add missing files to prevent memory gaps"]
}
```

### 正常系（推奨アクション）

#### 例 6: 生成可能なダイジェストあり

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

#### 例 7: 生成不可・ファイル不足

```json
{
  "status": "ok",
  "issues": [],
  "generatable_levels": [
    {"level": "weekly", "current": 3, "threshold": 5, "ready": false, "needed": 2}
  ],
  "recommendations": ["Add 2 more Loop files"]
}
```

#### 例 8: 複数階層生成可能

```json
{
  "status": "ok",
  "issues": [],
  "generatable_levels": [
    {"level": "weekly", "current": 10, "threshold": 5, "ready": true},
    {"level": "monthly", "current": 5, "threshold": 5, "ready": true}
  ],
  "recommendations": [
    "Run /digest weekly first",
    "Then run /digest monthly"
  ]
}
```

---

## 【重要】実装時の注意事項

> 📖 共通の実装ガイドラインである [_implementation-notes.md](../shared/_implementation-notes.md) を**必ず参照**してください。
> - UIメッセージの出力形式
> - config.py への依存
> - エラーハンドリング
> - 階層順序の維持
> - 実装時の優先順位

---

**このスキルは、EpisodicRAG システムの状態を分析し、最適なアクションを推奨します 📊**

---
