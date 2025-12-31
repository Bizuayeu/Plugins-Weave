---
name: expression
description: 表情システムの制御とビルドパイプライン
---

# /expression - 表情システムコマンド

Visual Expression（VEL）システムの制御とビルドパイプラインを提供するコマンドです。

## 目次

- [サブコマンド一覧](#サブコマンド一覧)
- [パターン1: /expression（ヘルプ表示）](#パターン1-expressionヘルプ表示)
- [パターン2: /expression forge（ビルドパイプライン）](#パターン2-expression-forgeビルドパイプライン)
- [パターン3: /expression build（HTML生成）](#パターン3-expression-buildhtml生成)
- [パターン4: /expression test（表情テスト）](#パターン4-expression-test表情テスト)

---

## サブコマンド一覧

| コマンド | 説明 |
|----------|------|
| `/expression` | ヘルプと使用可能な表情コード一覧を表示 |
| `/expression forge <path>` | 画像フォルダからJSONを生成 |
| `/expression build` | JSON+テンプレートからHTMLを生成 |
| `/expression test <key>` | 指定した表情のプレビュー |

---

## パターン1: /expression（ヘルプ表示）

引数なしで実行すると、表情システムのヘルプを表示します。

### 出力内容

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎭 VisualExpression システム
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

利用可能な表情コード（20種）:

Basic: 通常, 笑顔, 思考集中, 思考発散
Emotion: 喜び, 高揚, 驚き, 平穏
Negative: 怒り, 悲しみ, 激怒, 嫌悪
Anxiety: 不安, 恐れ, 動揺, 心配
Special: うとうと, 暗黒微笑, ぎゃふん, ぽやぽや

サブコマンド:
  /expression forge <path>  - 画像からJSON生成
  /expression build         - HTML生成
  /expression test <key>    - 表情テスト

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## パターン2: /expression forge（ビルドパイプライン）

画像フォルダを指定して、表情システム一式を生成します。

### 使用方法

```bash
/expression forge ~/images/avatar/
```

### 実行フロー

| Step | 実行内容 | 使用スクリプト |
|------|---------|---------------|
| 1 | 画像フォルダのスキャン | - |
| 2 | 画像→Base64変換 | `python generate_json.py <path>` |
| 3 | JSON出力確認 | - |
| 4 | HTML生成 | `python build_html.py` |
| 5 | 完了報告 | - |

### 実行例

```bash
cd {plugin_root}/scripts

# Step 2: JSON生成
python generate_json.py ~/images/avatar/ --output expression_images.json

# Step 4: HTML生成
python build_html.py \
    --template ../templates/ExpressionUI.template.html \
    --images expression_images.json \
    --output ExpressionUI.html
```

### 出力例

```
Scanning ~/images/avatar/...

  Added: normal <- Avatar_01_normal.jpg
  Added: smile <- Avatar_02_smile.jpg
  Added: focus <- Avatar_03_focus.jpg
  Added: joy <- Avatar_05_joy.jpg
  Added: calm <- Avatar_16_calm.jpg

Generated expression_images.json (125.3 KB)
Total expressions: 5

Built ExpressionUI.html (127.8 KB)
Embedded 5 expressions
```

---

## パターン3: /expression build（HTML生成）

既存のJSONファイルからHTMLのみを再生成します。

### 使用方法

```bash
/expression build
```

### 前提条件

- `expression_images.json` が存在すること

### 実行コマンド

```bash
cd {plugin_root}/scripts

python build_html.py \
    --template ../templates/ExpressionUI.template.html \
    --images expression_images.json \
    --output ExpressionUI.html
```

---

## パターン4: /expression test（表情テスト）

指定した表情キーでUIをプレビューします。

### 使用方法

```bash
/expression test elation
/expression test calm
/expression test cynical
```

### 使用可能なキー

| カテゴリ | キー |
|----------|------|
| Basic | normal, smile, focus, diverge |
| Emotion | joy, elation, surprise, calm |
| Negative | anger, sadness, rage, disgust |
| Anxiety | anxiety, fear, upset, worry |
| Special | sleepy, cynical, defeated, dreamy |

### 実行フロー

1. `ExpressionUI.html` の存在確認
2. sedコマンドで初期表情を変更
3. 変更後のHTMLをArtifactとして表示

```bash
sed 's/btns\[0\]\.click();/setExpr("elation");/' ExpressionUI.html
```

---

## 関連スキル

| スキル | 説明 |
|--------|------|
| `@auto-expression` | 表情自動付与ガイド |
| `@expression-forge` | ビルドパイプライン詳細 |

---

**VisualExpression** by Weave | [GitHub](https://github.com/Bizuayeu/Plugins-Weave)
