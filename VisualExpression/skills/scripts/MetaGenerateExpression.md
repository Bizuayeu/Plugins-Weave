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
| Hair Color | Main hair color | Orange, Blonde, Black |
| Hairstyle | Length & style | Long, Short, Ponytail |
| Eye Color | Iris color | Amber, Blue, Green |

### Optional Items

| Item | Description | Default |
|------|-------------|---------|
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
- Hair: [Hair Color], [Hairstyle]
- Eyes: [Eye Color]
- Outfit: [Outfit] (optional)
- Accessories: [Accessories] (optional)

Layout: 4 rows x 5 columns grid (20 expressions total)
Each column = 1 category (4 expressions per category, arranged vertically)
Each cell: Same character, same pose (bust shot), different facial expression

Col 1 (Basic): neutral, smile, focused thinking, creative thinking
Col 2 (Emotion): joy, elation/excitement, surprise, calm/peaceful
Col 3 (Negative): mild anger, sadness, rage, disgust
Col 4 (Anxiety): anxiety, fear, upset/confused, worried
Col 5 (Special): [Special1], [Special2], [Special3], [Special4]

Background: [Background]
Important: Keep character appearance consistent across all expressions.
Output as a single image with all 20 expressions arranged in a 4x5 grid (4 rows, 5 columns).
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

3. Tell me the hair color and hairstyle.
User: Orange long hair

4. What is the eye color?
User: Amber

5. What outfit? (Optional, can skip)
User: Kimono (Japanese traditional clothing)

6. Any accessories? (Optional)
User: None

7. What background style? (Default: simple gradient)
User: Golden gradient

8. Would you like to customize Special expressions (Row 5)?
   Default: sleepy, cynical, defeated, dreamy
User: Default is OK

Claude: Prompt generated. Copy & paste the following to Nano Banana Pro:

[Generated prompt]
```

---

## Notes

1. **Image Size**: Ideal generated image is 1400×1120px (280px × 4 rows × 5 cols)
2. **Consistency**: Emphasize to Nano Banana "keep character appearance consistent across all expressions"
3. **Regeneration**: If not perfect on first try, request corrections through dialogue
4. **Watermark**: Nano Banana Pro output may include watermarks

---

## Next Steps

After obtaining the generated image:

```bash
cd skills/scripts/MakeExpressionJson
python main.py your_grid_image.png --output ./output/
```

This generates:
- `ExpressionImages.json` - Base64 encoded image data
- `VisualExpressionUI.html` - Self-contained HTML
- `VisualExpressionSkills.zip` - For claude.ai upload

---

**VisualExpression** | [GitHub](https://github.com/Bizuayeu/Plugins-Weave)
