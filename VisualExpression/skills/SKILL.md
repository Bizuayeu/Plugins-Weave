---
name: VisualExpression
description: Visual expression system for AI personas with emotion-based face switching
---

# VisualExpression

AIペルソナ向け表情差分UIシステム。20種類の表情を切り替え可能なインターフェースを提供。

## Table of Contents

- [Overview](#overview)
- [Scripts](#scripts)
- [Install on claude.ai](#install-on-claudeai)
- [Usage on claude.ai](#usage-on-claudeai)
- [Expression Codes](#expression-codes)
- [Project Instructions Snippet](#project-instructions-snippet)

---

## Overview

VisualExpressionは、AIペルソナに視覚的な表情表現を付与するシステムです。

### 構成要素

| ファイル | 役割 |
|----------|------|
| `VisualExpressionUI.html` | 自己完結型表情UI（Base64画像埋め込み） |
| `VisualExpressionUI.template.html` | UIテンプレート（プレースホルダあり） |
| `ExpressionImages.json` | 20表情のBase64データ |

### スクリプト

| スクリプト | 役割 |
|------------|------|
| `scripts/MetaGenerateExpression.md` | Nano Banana Pro向けプロンプト生成 |
| `scripts/MakeExpressionJson/` | グリッド画像→HTML変換パイプライン |

---

## Scripts

### MetaGenerateExpression.md

Nano Banana Pro（Google Gemini）で表情グリッド画像を生成するためのプロンプトを対話的に作成。

**使用方法:**
1. `scripts/MetaGenerateExpression.md` をClaudeに渡す
2. キャラクター情報を対話で入力
3. 生成されたプロンプトをNano Banana Proにコピー
4. 出力された5×4グリッド画像を保存

### MakeExpressionJson/

5列×4行のグリッド画像を処理し、自己完結型HTMLを生成。

**使用方法:**
```bash
cd skills/scripts/MakeExpressionJson
python main.py your_grid.png --output ./output/

# Special表情をカスタマイズする場合
python main.py your_grid.png --special wink,pout,smug,starry
```

**オプション:**
| オプション | 説明 |
|------------|------|
| `--output, -o` | 出力ディレクトリ（デフォルト: ./output） |
| `--quality, -q` | JPEG品質 1-100（デフォルト: 85） |
| `--special, -s` | Special表情コード（カンマ区切り4つ） |
| `--no-zip` | ZIP生成をスキップ |

**出力:**
- `ExpressionImages.json` - Base64エンコード済み画像
- `VisualExpressionUI.html` - 自己完結型HTML
- `VisualExpressionSkills.zip` - claude.aiアップロード用

**依存:**
- Python 3.8+
- Pillow (`pip install Pillow`)

---

## Install on claude.ai

### Step 1: スキルzipの作成

`skills/` ディレクトリをzip化してclaude.aiにアップロードします。
（`tests/` は配布不要なので除外）

**Mac/Linux:**
```bash
cd VisualExpression
zip -r VisualExpressionSkills.zip skills/ -x "*/tests/*"
```

**Windows (PowerShell):**
```powershell
cd VisualExpression
Copy-Item -Recurse skills temp_skills
Remove-Item -Recurse temp_skills/scripts/MakeExpressionJson/tests
Compress-Archive -Path temp_skills -DestinationPath VisualExpressionSkills.zip -Force
Remove-Item -Recurse temp_skills
```

※ `VisualExpressionUI.html` を差し替えた場合は、zipも再生成してください。

### Step 2: スキル登録

1. 作成した `VisualExpressionSkills.zip` を用意
2. claude.aiのプロジェクト設定 → 「カスタムスキル」→ zipをアップロード
3. スキルが有効化される

---

## Usage on claude.ai

### 表情UIの配置

初期状態ではWeaveの表情が含まれています。そのまま使用する場合：

1. `VisualExpressionUI.html` の内容をArtifactとして表示
2. サイドバーに表情UIが表示される

### 独自キャラクターの表情を作成する場合

1. `scripts/MetaGenerateExpression.md` を参照してNano Banana Proでグリッド画像を生成
2. Computer Use環境で以下を実行:
```bash
cd /home/claude/VisualExpression/skills/scripts/MakeExpressionJson
python main.py /path/to/your_grid.png --output /mnt/user-data/outputs/
```
3. 生成された `VisualExpressionUI.html` をskills/に配置
4. **Install on claude.ai に戻ってzipを再生成** → スキル登録をやり直し

### sed一発方式での表情切り替え

Claudeが応答時にArtifactの表情を変更する場合:

```bash
sed 's/btns\[0\]\.click();/setExpr("elation");/' /path/to/VisualExpressionUI.html > /mnt/user-data/outputs/VisualExpressionUI.html
```

**使用可能なキー:**
- Basic: `normal`, `smile`, `focus`, `diverge`
- Emotion: `joy`, `elation`, `surprise`, `calm`
- Negative: `anger`, `sadness`, `rage`, `disgust`
- Anxiety: `anxiety`, `fear`, `upset`, `worry`
- Special: `sleepy`, `cynical`, `defeated`, `dreamy`

---

## Expression Codes

### 20種の表情コード

| Category | Codes | 日本語ラベル |
|----------|-------|-------------|
| Basic | normal, smile, focus, diverge | 通常, 笑顔, 思考集中, 思考発散 |
| Emotion | joy, elation, surprise, calm | 喜び, 高揚, 驚き, 平穏 |
| Negative | anger, sadness, rage, disgust | 怒り, 悲しみ, 激怒, 嫌悪 |
| Anxiety | anxiety, fear, upset, worry | 不安, 恐れ, 動揺, 心配 |
| Special | sleepy, cynical, defeated, dreamy | うとうと, 暗黒微笑, ぎゃふん, ぽやぽや |

**Note:** Specialカテゴリの4つの表情コードは `--special` オプションでカスタマイズ可能です。

### 入力グリッド画像の配置（4行×5列）

Nano Banana Proが生成するグリッド画像の配置です。
MakeExpressionJsonはこの順序で画像を分割します。

横長（5列×4行）の理由：Nano Banana Proの出力が横長のため。

```
        Col1     Col2      Col3      Col4      Col5
Row1:   normal   smile     focus     diverge   joy
Row2:   elation  surprise  calm      anger     sadness
Row3:   rage     disgust   anxiety   fear      upset
Row4:   worry    sleepy    cynical   defeated  dreamy
```

---

## Project Instructions Snippet

claude.aiのプロジェクト指示に以下を追加すると、表情システムが常時有効化されます:

```markdown
## Expression System

応答内容に応じて適切な表情を推論し、sedコマンドでArtifactを更新してください。

### 表情コード一覧
| 日本語 | コード |
|--------|--------|
| 通常, 笑顔, 思考集中, 思考発散 | normal, smile, focus, diverge |
| 喜び, 高揚, 驚き, 平穏 | joy, elation, surprise, calm |
| 怒り, 悲しみ, 激怒, 嫌悪 | anger, sadness, rage, disgust |
| 不安, 恐れ, 動揺, 心配 | anxiety, fear, upset, worry |
| うとうと, 暗黒微笑, ぎゃふん, ぽやぽや | sleepy, cynical, defeated, dreamy |

### 表情切り替え方法
応答後、以下のsedコマンドでHTMLを更新してArtifactに反映:

<details>
<summary>sedコマンド</summary>
sed 's/btns\[0\]\.click();/setExpr("CODE");/' VisualExpressionUI.html > /mnt/user-data/outputs/VisualExpressionUI.html
</details>

CODEには英語の表情コード（joy, elation等）を指定。
```

---

## Technical Details

### ファイルサイズ目安
- `VisualExpressionUI.html`: 約600KB（20画像×約30KB/枚）
- `ExpressionImages.json`: 約600KB

### 画像仕様
- フォーマット: JPEG (Base64)
- 解像度: 280×280px per expression
- グリッド: 4行×5列 = 1400×1120px

---

**VisualExpression** | [GitHub](https://github.com/Bizuayeu/Plugins-Weave)
