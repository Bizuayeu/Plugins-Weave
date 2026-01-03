# AnalyzeExpressionOffset

[English] | [日本語](AnalyzeExpressionOffset.jp.md)

Meta-script for Claude to analyze expression grid images and determine optimal crop offsets.

## Overview

This script enables Claude (Weave) to visually analyze expression grid images and output offset configurations for center-cropping each expression at its visual center rather than the geometric cell center.

## Usage

1. Pass this file to Claude along with the expression grid image
2. Claude analyzes each cell's expression position
3. Claude outputs an offset JSON configuration
4. Use the JSON with `MakeExpressionJson/main.py --offsets`

---

## Analysis Instructions

### Grid Layout

The input image is a 4-row × 5-column grid (20 expressions total):
- Each cell: 300×300 pixels
- Total image: 1500×1200 pixels
- Output per cell: 280×280 pixels (center-cropped with 10px margin)

### Expression Code Mapping

| Position | Col 1 (Basic) | Col 2 (Emotion) | Col 3 (Negative) | Col 4 (Anxiety) | Col 5 (Special) |
|----------|---------------|-----------------|------------------|-----------------|-----------------|
| Row 1 | normal | joy | anger | anxiety | sleepy |
| Row 2 | smile | elation | sadness | fear | cynical |
| Row 3 | focus | surprise | rage | upset | defeated |
| Row 4 | diverge | calm | disgust | worry | dreamy |

### Visual Analysis Process

For each expression cell:

1. **Locate the face center**
   - Find the midpoint between the eyes (or equivalent facial feature)
   - This is the "expression center"

2. **Compare with cell center**
   - Cell geometric center: (150, 150) within each 300×300 cell
   - Expression center may differ due to:
     - Character pose variations
     - Head tilt or turn
     - Artistic asymmetry

3. **Calculate offset**
   - Offset X = (Expression center X) - 150
   - Offset Y = (Expression center Y) - 150
   - Positive X = expression is right of center → crop should shift right
   - Positive Y = expression is down from center → crop should shift down

### Offset Guidelines

- **Small offsets (±1-5px)**: Minor adjustments, common for slight variations
- **Medium offsets (±6-15px)**: Noticeable shift, typical for dynamic poses
- **Large offsets (±16-20px)**: Maximum recommended; larger suggests generation issues
- **Zero offset**: Expression is perfectly centered; use `{}` or omit from JSON

---

## Output Format

### JSON Structure

```json
{
  "offsets": {
    "normal": {"x": 0, "y": -3},
    "smile": {"x": 2, "y": 0},
    "joy": {"x": -5, "y": 2},
    "anger": {"x": 0, "y": 0}
  },
  "analysis_notes": "Most expressions well-centered. joy shifted left, applied +5 correction.",
  "recommended_regenerate": []
}
```

### Field Descriptions

| Field | Description |
|-------|-------------|
| `offsets` | Dictionary of expression code → {x, y} offset pairs |
| `offsets.{code}.x` | Horizontal offset in pixels (positive = right) |
| `offsets.{code}.y` | Vertical offset in pixels (positive = down) |
| `analysis_notes` | Optional notes about the analysis |
| `recommended_regenerate` | List of expression codes that should be regenerated |

### Omission Rules

- Expressions with zero offset (perfectly centered) can be omitted
- If all expressions are centered, output: `{"offsets": {}}`

---

## Example Analysis

### Sample Dialogue

```
User: [Attaches expression grid image] Please analyze this expression grid and determine crop offsets.

Claude: I'll analyze each expression cell for optimal cropping.

**Analysis Results:**

Looking at the grid, I notice:
- Row 1-2: Expressions are well-centered
- Row 3: Some expressions have the face slightly higher (head tilt in focus/rage)
- Row 4: The dreamy expression has a slight rightward lean

**Offset Configuration:**

{
  "offsets": {
    "focus": {"x": 0, "y": -5},
    "rage": {"x": 0, "y": -3},
    "dreamy": {"x": 4, "y": 0}
  },
  "analysis_notes": "Most expressions centered. Focus/rage have upward head tilt. Dreamy leans right.",
  "recommended_regenerate": []
}

Copy this JSON and use with:
python main.py grid_image.png --offsets offsets.json
```

---

## Integration with MakeExpressionJson

### Command Line Usage

```bash
# Save offset JSON to file
echo '{"offsets": {"focus": {"x": 0, "y": -5}}}' > offsets.json

# Run with offsets
python main.py grid_image.png --offsets offsets.json --output ./output/
```

### Programmatic Usage

```python
from usecases.image_splitter import ImageSplitter

offsets = {
    "focus": {"x": 0, "y": -5},
    "rage": {"x": 0, "y": -3},
    "dreamy": {"x": 4, "y": 0}
}

splitter = ImageSplitter(offsets=offsets)
results = splitter.split_from_file("grid_image.png")
```

---

## Notes

1. **Precision**: Offsets are in pixels; ±1-2px adjustments are usually imperceptible
2. **Consistency**: Apply similar offsets to expressions with similar poses
3. **Limits**: Maximum recommended offset is ±20px; larger values suggest the cell needs regeneration
4. **CHIBI expressions**: Row 3-4 of Special column may have different proportions; adjust accordingly

---

**VisualExpression** | [GitHub](https://github.com/Bizuayeu/Plugins-Weave)
