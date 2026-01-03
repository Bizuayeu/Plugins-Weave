# MetaGenerateExpression

[English] | [日本語](MetaGenerateExpression.jp.md)

Meta-script for interactively generating expression grid prompts for Nano Banana Pro.

## Overview

This script collects character information through dialogue and outputs
prompts for generating 4-row × 5-column expression grid images with
Nano Banana Pro (Google Gemini).

## Usage

1. Pass this file to Claude (claude.ai or Claude Code)
2. Claude interactively collects character information
3. Copy & paste the generated prompt to Nano Banana Pro
4. Process the generated image with `MakeExpressionJson/main.py`

---

## Data Collection Items

### Required Items

| Item | Description | Example |
|------|-------------|---------|
| Character Name | Display name | Weave, Alice, Protagonist |
| Art Style | Visual style | Anime, Realistic, Icon-like |
| Skin Tone | Skin color/texture | Fair, Tan, Brown |
| Hair Color | Main hair color | Orange, Blonde, Black |
| Hairstyle | Length & style | Long, Short, Ponytail |

### Optional Items

| Item | Description | Default |
|------|-------------|---------|
| Eye Color | Iris color | Auto (based on character) |
| Outfit | Basic clothing | Kimono, Uniform, Casual |
| Accessories | Hair accessories, etc. | None |
| Background | Background style | Simple gradient |
| Special Expression Customization | 4 special expressions | sleepy, cynical, defeated, dreamy |

---

## Expression Codes (20 types)

For detailed expression codes, see [SKILL.md Expression Codes](../SKILL.md#expression-codes).

### Overview (5 categories × 4 expressions = 20 types)

| Category | Expression Codes |
|----------|-----------------|
| Basic | normal, smile, focus, diverge |
| Emotion | joy, elation, surprise, calm |
| Negative | anger, sadness, rage, disgust |
| Anxiety | anxiety, fear, upset, worry |
| Special | sleepy, cynical, defeated, dreamy |

*Note: Special category can be customized with `--special` option*

---

## Prompt Generation Template

Generate prompts in the following format from collected information:

```
Create a character expression sheet for [Character Name].

Art style: [Art Style]

Character details:
- Skin: [Skin Tone]
- Hair: [Hair Color], [Hairstyle]
- Eyes: [Eye Color] (optional)
- Outfit: [Outfit] (optional)
- Accessories: [Accessories] (optional)

Layout: 4 rows x 5 columns grid (20 expressions total)
Each cell: 300x300 pixels (total image size: 1500x1200 pixels)
Each column = 1 category (4 expressions per category, arranged vertically)
Each cell: Same character, same pose (bust shot), different facial expression

Col 1 (Basic): neutral, smile, focused thinking, creative thinking
Col 2 (Emotion): joy, elation/excitement, surprise, calm/peaceful
Col 3 (Negative): mild anger, sadness, rage, disgust
Col 4 (Anxiety): anxiety, fear, upset/confused, worried
Col 5 (Special): [Special1], [Special2], [Special3] (CHIBI/deformed style), [Special4] (CHIBI/deformed style)

Background: [Background]
Important: Keep character appearance consistent across all expressions.
Output as a single image with all 20 expressions arranged in a 4x5 grid (4 rows, 5 columns), total size 1500x1200 pixels is MANDATORY!!!
```

---

## Example

### Claude Dialogue Flow

```
Claude: Tell me about the character you want to generate expressions for.

1. What is the character's name?
User: Weave

2. What art style? (Anime, Realistic, Icon-like, etc.)
User: Anime style

3. What is the skin tone? (Fair, Tan, Brown, etc.)
User: Fair

4. Tell me the hair color and hairstyle.
User: Orange long hair

5. What is the eye color? (Optional, can skip)
User: Amber

6. What outfit? (Optional, can skip)
User: Kimono (Japanese traditional clothing)

7. Any accessories? (Optional)
User: None

8. What background style? (Default: simple gradient)
User: Golden gradient

9. Would you like to customize Special expressions (Col 5)?
   Default: sleepy, cynical, defeated, dreamy
   Note: Row 3,4 will be generated in CHIBI style
User: Default is OK

Claude: Prompt generated. Copy & paste the following to Nano Banana Pro:

[Generated prompt]
```

---

## Notes

1. **Image Size**: Generated image must be **1500×1200px** (300px × 4 rows × 5 cols)
   - Center 280px is cropped from each 300px cell to absorb positioning errors
2. **Consistency**: Emphasize to Nano Banana "keep character appearance consistent across all expressions"
3. **Regeneration**: If not perfect on first try, request corrections through dialogue
4. **Watermark**: Nano Banana Pro output may include watermarks
5. **Expression Center Offset (Optional)**: If the visual center of expressions differs from cell center,
   use [AnalyzeExpressionOffset.md](AnalyzeExpressionOffset.md) to have Claude determine optimal offsets

---

## Next Steps

After obtaining the generated image:

### Basic Usage

```bash
cd skills/scripts/MakeExpressionJson
python main.py your_grid_image.png --output ./output/
```

### Using Offset Analysis (Optional)

If expressions are misaligned, first have Claude analyze the image:

1. Pass `AnalyzeExpressionOffset.md` and the image to Claude
2. Save Claude's output JSON as `offsets.json`
3. Run with offsets:

```bash
python main.py your_grid_image.png --offsets offsets.json --output ./output/
```

### Output Files

- `ExpressionImages.json` - Base64 encoded image data
- `VisualExpressionUI.html` - Self-contained HTML
- `VisualExpressionSkills.zip` - For claude.ai upload

---

**VisualExpression** | [GitHub](https://github.com/Bizuayeu/Plugins-Weave)
