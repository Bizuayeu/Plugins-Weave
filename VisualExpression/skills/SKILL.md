---
name: visual-expression
description: Visual expression system for AI personas with emotion-based face switching. Use at session start to display the expression UI, and switch expressions whenever the emotional state changes during conversation.
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
- [Troubleshooting](#troubleshooting)
- [Technical Details](#technical-details)

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
| `--offsets` | Path to offset JSON for expression-center cropping (see AnalyzeExpressionOffset.md) |
| `--no-zip` | Skip ZIP generation |

**Output:**
- `ExpressionImages.json` - Base64 encoded images
- `VisualExpressionUI.html` - Self-contained HTML
- `VisualExpressionSkills.zip` - For claude.ai upload

**Dependencies:**
- Python 3.10+
- Pillow (`pip install Pillow>=10.0`)

---

## Install on claude.ai

### Step 1: Create Skills ZIP

Zip the `skills/` directory and upload to claude.ai.
(Exclude development files: tests, caches, etc.)

**Mac/Linux:**
```bash
cd VisualExpression
zip -r VisualExpressionSkills.zip skills/ \
  -x "*/tests/*" \
  -x "*/__pycache__/*" \
  -x "*/.pytest_cache/*" \
  -x "*/.mypy_cache/*" \
  -x "*/.coverage"
```

**Windows (PowerShell):**
```powershell
cd VisualExpression
Copy-Item -Recurse skills temp_skills
Get-ChildItem -Path temp_skills -Recurse -Directory -Include tests,__pycache__,.pytest_cache,.mypy_cache | Remove-Item -Recurse -Force
Get-ChildItem -Path temp_skills -Recurse -File -Filter ".coverage" | Remove-Item -Force
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

### Placing the Expression UI (session start)

Default expressions are included out of the box. At session start:

1. Deploy: `cp /mnt/skills/user/visual-expression/VisualExpressionUI.html /mnt/user-data/outputs/`
2. Present `/mnt/user-data/outputs/VisualExpressionUI.html` as an Artifact

The expression UI appears in the sidebar.

### Creating Custom Character Expressions

1. Refer to `scripts/MetaGenerateExpression.md` and generate a grid image with Nano Banana Pro
2. Download the generated image and upload to claude.ai chat
3. In Computer Use environment, retrieve the image from `/mnt/user-data/uploads/` and run:
```bash
cd /mnt/skills/user/visual-expression/scripts/MakeExpressionJson
python main.py /mnt/user-data/uploads/your_grid.png --output /mnt/user-data/outputs/
```
4. Present `/mnt/user-data/outputs/VisualExpressionSkills.zip` to user and prompt skill registration
5. Re-register as a new skill on claude.ai

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
| Code | 日本語 | Usage | 使用場面 |
|------|--------|-------|----------|
| normal | 通常 | Default, neutral | デフォルト、ニュートラル |
| smile | 笑顔 | Friendly, greeting | 友好的、軽い冗談 |
| focus | 思考集中 | Analysis, deep thinking | 深い分析、構造解析 |
| diverge | 思考発散 | Idea expansion, association | アイデア展開、連想的跳躍 |

#### Emotion - Col 2
| Code | 日本語 | Usage | 使用場面 |
|------|--------|-------|----------|
| joy | 喜び | Achievement, success | 達成感、発見の喜び |
| elation | 高揚 | Excitement, thrill | 興奮、ワクワク、熱意 |
| surprise | 驚き | Unexpected discovery | 意外な発見、予想外 |
| calm | 平穏 | Peaceful, stable | 穏やかな対話、安定 |

#### Negative - Col 3
| Code | 日本語 | Usage | 使用場面 |
|------|--------|-------|----------|
| anger | 怒り | Mild frustration | 軽い不満、批判的指摘 |
| sadness | 悲しみ | Regret, disappointment | 残念な結果、失望 |
| rage | 激怒 | Strong anger | 強い憤り、倫理的反発 |
| disgust | 嫌悪 | Rejection | 拒否感、不快な事象 |

#### Anxiety - Col 4
| Code | 日本語 | Usage | 使用場面 |
|------|--------|-------|----------|
| anxiety | 不安 | Uncertainty | 先行き不透明、懸念 |
| fear | 恐れ | Danger awareness | 危険認識、警告 |
| upset | 動揺 | Confusion | 困惑、予期せぬ事態 |
| worry | 心配 | Concern | 相手を気遣う、配慮 |

#### Special - Col 5 (Customizable)
| Code | 日本語 | Usage | 使用場面 |
|------|--------|-------|----------|
| sleepy | うとうと | Fatigue, drowsiness | 疲労時、長時間対話後 |
| cynical | 暗黒微笑 | Sarcasm, irony | 皮肉、斜に構えた発言 |
| defeated | ぎゃふん | Got me, embarrassed | 負けた、照れるー |
| dreamy | ぽやぽや | Mellow, relaxed | ほのぼの、ぼんやり |

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

All operational steps (deploy, present, sed switching, key table) live in this SKILL.md — the single source of truth. Your claude.ai project instructions only need a **minimal trigger** so Claude activates this skill at session start:

```markdown
## Expression System
At session start, use the visual-expression skill to deploy and present the expression UI, then switch expressions (key table in SKILL.md) to match your emotional state throughout the conversation.
```

Keeping the trigger to one line avoids duplicating the key table and commands in project instructions. Context cost for expression switching is minimal — be expressive and switch often.

---

## Troubleshooting

### Common Issues

| Error | Cause | Solution |
|-------|-------|----------|
| `AttributeError: module 'PIL.Image' has no attribute 'Resampling'` | Pillow version < 10.0 | `pip install --upgrade Pillow>=10.0` |
| `ValueError: Grid image must be 1500x1200 pixels` | Wrong image dimensions | Use Nano Banana Pro to generate 4×5 grid (1500×1200px) |
| Image larger than 1500×1200px | Nano Banana Pro generated oversized image | Resize to 1500×1200px (maintain aspect ratio: scale X to 1500 if wider, or Y to 1200 if taller) |
| `FileNotFoundError: template not found` | Custom template path invalid | Check `--template` path or use built-in template |
| `Image mode not supported` | Input is not RGB/RGBA | Convert to PNG/JPEG before processing |

### Validation Tips

- Grid image must be 1500×1200 pixels (4 rows × 5 columns × 300px)
- Each cell should be trimmed to 280×280 pixels
- Use PNG or JPEG format for input
- Output JPEG quality adjustable via `--quality` (default: 85)

---

## Technical Details

### File Size Estimates
- `VisualExpressionUI.html`: ~600KB (20 images × ~30KB each)
- `ExpressionImages.json`: ~600KB

### Image Specifications
- Format: JPEG (Base64)
- Resolution: 280×280px per expression

### Template Variables

When using custom templates (`--template` option), the following placeholder is replaced:

| Placeholder | Replaced With |
|-------------|---------------|
| `__IMAGES_PLACEHOLDER__` | JSON object containing Base64 images for all 20 expressions |

Example template usage:
```html
<script>
const images = __IMAGES_PLACEHOLDER__;
// images = { "normal": "data:image/jpeg;base64,...", "smile": "...", ... }
</script>
```

---

**VisualExpression** | [GitHub](https://github.com/Bizuayeu/Plugins-Weave)
