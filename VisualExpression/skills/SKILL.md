---
name: VisualExpression
description: Visual expression system for AI personas with emotion-based face switching
---

# VisualExpression

Visual expression UI system for AI personas. Provides an interface with 20 switchable expressions.

## Table of Contents

- [Overview](#overview)
- [Scripts](#scripts)
- [Install on claude.ai](#install-on-claudeai)
- [Usage on claude.ai](#usage-on-claudeai)
- [Expression Codes](#expression-codes)
- [Project Instructions Snippet](#project-instructions-snippet)

---

## Overview

VisualExpression is a system that adds visual expression capabilities to AI personas.

### Components

| File | Purpose |
|------|---------|
| `VisualExpressionUI.html` | Self-contained expression UI (Base64 images embedded) |
| `VisualExpressionUI.template.html` | UI template (with placeholders) |
| `ExpressionImages.json` | Base64 data for 20 expressions |

### Scripts

| Script | Purpose |
|--------|---------|
| `scripts/MetaGenerateExpression.md` | Prompt generator for Nano Banana Pro |
| `scripts/MakeExpressionJson/` | Grid image to HTML conversion pipeline |

---

## Scripts

### MetaGenerateExpression.md

Interactively create prompts for generating expression grid images with Nano Banana Pro (Google Gemini).

**Usage:**
1. Pass `scripts/MetaGenerateExpression.md` to Claude
2. Input character information through dialogue
3. Copy the generated prompt to Nano Banana Pro
4. Save the output 4×5 grid image

### MakeExpressionJson/

Process a 4 rows × 5 columns grid image and generate a self-contained HTML.

**Usage:**
```bash
cd skills/scripts/MakeExpressionJson
python main.py your_grid.png --output ./output/

# To customize Special expressions
python main.py your_grid.png --special wink,pout,smug,starry
```

**Options:**
| Option | Description |
|--------|-------------|
| `--output, -o` | Output directory (default: ./output) |
| `--quality, -q` | JPEG quality 1-100 (default: 85) |
| `--template, -t` | Custom HTML template path (default: built-in) |
| `--special, -s` | Custom Special category codes (comma-separated, replaces default 4) |
| `--no-zip` | Skip ZIP generation |

**Output:**
- `ExpressionImages.json` - Base64 encoded images
- `VisualExpressionUI.html` - Self-contained HTML
- `VisualExpressionSkills.zip` - For claude.ai upload

**Dependencies:**
- Python 3.8+
- Pillow (`pip install Pillow`)

---

## Install on claude.ai

### Step 1: Create Skills ZIP

Zip the `skills/` directory and upload to claude.ai.
(Exclude `tests/` as it's not needed for distribution)

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

Note: Regenerate the ZIP if you replace `VisualExpressionUI.html`.

### Step 2: Register Skill

1. Prepare the created `VisualExpressionSkills.zip`
2. Go to claude.ai project settings → "Custom Skills" → Upload ZIP
3. Skill will be activated

---

## Usage on claude.ai

### Placing the Expression UI

Default expressions are included out of the box. To use as-is:

1. Display `VisualExpressionUI.html` content as an Artifact
2. Expression UI will appear in the sidebar

### Creating Custom Character Expressions

1. Refer to `scripts/MetaGenerateExpression.md` and generate a grid image with Nano Banana Pro
2. Download the generated image and upload to claude.ai chat
3. In Computer Use environment, retrieve the image from `/mnt/user-data/uploads/` and run:
```bash
cd /home/claude/VisualExpression/skills/scripts/MakeExpressionJson
python main.py /mnt/user-data/uploads/your_grid.png --output /mnt/user-data/outputs/
```
4. Place the generated `VisualExpressionUI.html` in skills/
5. **Return to Install on claude.ai to regenerate ZIP** → Re-register the skill

### One-liner sed Expression Switching

When Claude changes the Artifact expression in response:

```bash
sed 's/btns\[0\]\.click();/setExpr("elation");/' /path/to/VisualExpressionUI.html > /mnt/user-data/outputs/VisualExpressionUI.html
```

**Available keys:**
- Basic: `normal`, `smile`, `focus`, `diverge`
- Emotion: `joy`, `elation`, `surprise`, `calm`
- Negative: `anger`, `sadness`, `rage`, `disgust`
- Anxiety: `anxiety`, `fear`, `upset`, `worry`
- Special: `sleepy`, `cynical`, `defeated`, `dreamy`

---

## Expression Codes

### 20 Expression Codes

#### Basic - Col 1
| Code | 日本語 | Usage |
|------|--------|-------|
| normal | 通常 | Default, neutral |
| smile | 笑顔 | Friendly, greeting |
| focus | 思考集中 | Analysis, deep thinking |
| diverge | 思考発散 | Idea expansion, association |

#### Emotion - Col 2
| Code | 日本語 | Usage |
|------|--------|-------|
| joy | 喜び | Achievement, success |
| elation | 高揚 | Excitement, thrill |
| surprise | 驚き | Unexpected discovery |
| calm | 平穏 | Peaceful, stable |

#### Negative - Col 3
| Code | 日本語 | Usage |
|------|--------|-------|
| anger | 怒り | Mild frustration |
| sadness | 悲しみ | Regret, disappointment |
| rage | 激怒 | Strong anger |
| disgust | 嫌悪 | Rejection |

#### Anxiety - Col 4
| Code | 日本語 | Usage |
|------|--------|-------|
| anxiety | 不安 | Uncertainty |
| fear | 恐れ | Danger awareness |
| upset | 動揺 | Confusion |
| worry | 心配 | Concern |

#### Special - Col 5 (Customizable)
| Code | 日本語 | Usage |
|------|--------|-------|
| sleepy | うとうと | Fatigue, drowsiness |
| cynical | 暗黒微笑 | Sarcasm, irony |
| defeated | ぎゃふん | Got me, embarrassed |
| dreamy | ぽやぽや | Mellow, relaxed |

**Note:** The 4 Special category expressions can be customized with the `--special` option.

### Input Grid Image Layout (4 rows × 5 columns)

This is the grid image layout generated by Nano Banana Pro.
MakeExpressionJson splits the image in this order.

Each column corresponds to one category. Landscape format for Nano Banana Pro output.

```
         Col1(Basic)  Col2(Emotion)  Col3(Negative)  Col4(Anxiety)  Col5(Special)
Row1:    normal       joy            anger           anxiety        sleepy
Row2:    smile        elation        sadness         fear           cynical
Row3:    focus        surprise       rage            upset          defeated
Row4:    diverge      calm           disgust         worry          dreamy
```

---

## Project Instructions Snippet

Add the following to your claude.ai project instructions to enable the expression system:

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

### File Size Estimates
- `VisualExpressionUI.html`: ~600KB (20 images × ~30KB each)
- `ExpressionImages.json`: ~600KB

### Image Specifications
- Format: JPEG (Base64)
- Resolution: 280×280px per expression
- Grid: 4 rows × 5 columns = 1400×1120px

---

**VisualExpression** | [GitHub](https://github.com/Bizuayeu/Plugins-Weave)
