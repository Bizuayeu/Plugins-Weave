---
name: expression-forge
description: 立ち絵からの表情システム構築パイプライン
---

# expression-forge - 表情システムビルダー

ユーザーが提供する立ち絵画像から、Claude.ai Artifact用の表情システム一式を構築します。
`expression_images.json` + `ExpressionUI.html` を自動生成します。

## 目次

- [概要](#概要)
- [入力要件](#入力要件)
- [実行フロー](#実行フロー)
- [出力物](#出力物)
- [画像がない場合のガイド](#画像がない場合のガイド)

---

## 概要

### 処理フロー

```
画像フォルダ → generate_json.py → expression_images.json
                                          ↓
テンプレート + JSON → build_html.py → ExpressionUI.html
```

### 必要環境

- Python 3.8+（標準ライブラリのみ）
- 画像ファイル（JPEG/PNG）

---

## 入力要件

### 画像ファイル仕様

| 項目 | 仕様 |
|------|------|
| 形式 | JPEG推奨（PNG可） |
| 解像度 | 280x280px 推奨 |
| 背景 | 透過または単色 |
| 枚数 | 最低1枚、推奨5-20枚 |

### 命名規則

```
{prefix}_{番号}_{key}.{ext}

例:
Avatar_01_normal.jpg
Avatar_02_smile.jpg
Avatar_03_focus.jpg
Avatar_04_diverge.jpg
Avatar_05_joy.jpg
```

**ファイル名からキーを抽出**：
- `_01_normal.jpg` → `normal`
- `_02_smile.jpg` → `smile`

### 使用可能なキー（20種）

| カテゴリ | キー |
|----------|------|
| Basic | normal, smile, focus, diverge |
| Emotion | joy, elation, surprise, calm |
| Negative | anger, sadness, rage, disgust |
| Anxiety | anxiety, fear, upset, worry |
| Special | sleepy, cynical, defeated, dreamy |

---

## 実行フロー

### Step 1: 画像→JSON変換

```bash
cd {plugin_root}/scripts
python generate_json.py ~/images/avatar/ --output expression_images.json
```

**出力例**:
```
  Added: normal <- Avatar_01_normal.jpg
  Added: smile <- Avatar_02_smile.jpg
  Added: focus <- Avatar_03_focus.jpg

Generated expression_images.json (150.2 KB)
Total expressions: 5
```

### Step 2: HTML生成

```bash
python build_html.py \
  --template ../templates/ExpressionUI.template.html \
  --images expression_images.json \
  --output ExpressionUI.html
```

**出力例**:
```
Built ExpressionUI.html (152.5 KB)
```

### Step 3: Artifactへ展開

生成された `ExpressionUI.html` をClaude.ai WebUIのArtifactに渡します。

---

## 出力物

| ファイル | サイズ目安 | 用途 |
|----------|-----------|------|
| `expression_images.json` | 30-600KB | Base64画像データ |
| `ExpressionUI.html` | 30-650KB | Artifact用HTML |

### expression_images.json 構造

```json
{
  "normal": "data:image/jpeg;base64,/9j/4AAQ...",
  "smile": "data:image/jpeg;base64,/9j/4AAQ...",
  "focus": "data:image/jpeg;base64,/9j/4AAQ..."
}
```

### ExpressionUI.html 機能

- 280x280px 表情画像表示
- カテゴリ別ボタン（Basic/Emotion/Negative/Anxiety/Special）
- テキスト入力による表情制御
- `setExpr("key")` 関数で外部からの制御

---

## 画像がない場合のガイド

### 推奨表情セット

**最小構成（5種）**:
```
normal, smile, focus, joy, calm
```

**標準構成（10種）**:
```
normal, smile, focus, diverge, joy,
elation, surprise, calm, worry, dreamy
```

**完全構成（20種）**:
```
全20種（Weave表情システム準拠）
```

### 画像生成のヒント

1. **AI画像生成サービスを使用**
   - 同一キャラクターで複数表情を生成
   - プロンプト例：`anime character, orange hair, [expression], bust shot, white background`

2. **表情差分の作成**
   - 目・眉・口の変化で表情を作り分け
   - 同一構図・同一キャラクターを維持

3. **リサイズ**
   - 280x280px にリサイズ
   - 顔が中心になるようトリミング

4. **ファイル命名**
   - 命名規則に従ってリネーム
   - `{prefix}_01_normal.jpg` 形式

---

## Artifact連携

### sedコマンドによる表情制御

生成されたHTMLの表情を変更するには：

```bash
sed 's/btns\[0\]\.click();/setExpr("calm");/' ExpressionUI.html > output.html
```

### 使用可能なキー

```javascript
setExpr("normal")   // 通常
setExpr("smile")    // 笑顔
setExpr("focus")    // 思考集中
setExpr("elation")  // 高揚
setExpr("calm")     // 平穏
setExpr("cynical")  // 暗黒微笑
setExpr("dreamy")   // ぽやぽや
// ... 全20種
```

---

**VisualExpression** by Weave | [GitHub](https://github.com/Bizuayeu/Plugins-Weave)
