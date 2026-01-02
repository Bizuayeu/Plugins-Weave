# VisualExpression

Visual expression system for AI personas with emotion-based face switching.

## Table of Contents

- [Quick Start](#quick-start)
- [Documentation Map](#documentation-map)
- [Features](#features)
- [See Also](#see-also)

---

## Quick Start

1. Generate expression grid image using Nano Banana Pro (see `skills/scripts/MetaGenerateExpression.md`)
2. Run `python main.py your_grid.png` to build HTML
3. Upload generated zip to claude.ai or install as Claude Code plugin

---

## Documentation Map

| File | For | Content |
|------|-----|---------|
| [README.md](README.md) | Everyone | Quick start (this file) |
| [skills/SKILL.md](skills/SKILL.md) | Users | Full documentation |
| [skills/scripts/MetaGenerateExpression.md](skills/scripts/MetaGenerateExpression.md) | Users | Nano Banana Pro prompt generator |
| [skills/scripts/MakeExpressionJson/](skills/scripts/MakeExpressionJson/) | Developers | Image processing pipeline |

---

## Features

- **20 Expression Variations**: 5 categories x 4 expressions each
- **Nano Banana Pro Integration**: Meta-script for generating expression grids
- **One-Click Build**: Grid image to HTML with Base64 embedded images
- **Cross-Platform**: Works on both claude.ai and Claude Code
- **sed-based Switching**: Fast expression changes via single command

---

## See Also

- [skills/SKILL.md](skills/SKILL.md) - Full usage guide
- [GitHub](https://github.com/Bizuayeu/Plugins-Weave) - Source repository

---

**VisualExpression** | [GitHub](https://github.com/Bizuayeu/Plugins-Weave)
