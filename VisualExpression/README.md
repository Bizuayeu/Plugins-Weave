English | [日本語](README.jp.md)

# VisualExpression

Visual expression system for AI personas with emotion-based face switching.

## Table of Contents

- [Quick Start](#quick-start)
- [Documentation Map](#documentation-map)
- [Features](#features)
- [See Also](#see-also)

---

## Prerequisites

- Python 3.10+
- Pillow 10.0+ (`pip install Pillow>=10.0`)

---

## Quick Start

1. Generate expression grid image using Nano Banana Pro (see `skills/scripts/MetaGenerateExpression.md`)
2. Build HTML from grid image:
   ```bash
   cd skills/scripts/MakeExpressionJson
   python main.py your_grid.png
   ```
3. Upload generated zip to claude.ai or install as Claude Code plugin

---

## Documentation Map

| File | For | Content |
|------|-----|---------|
| [README.md](README.md) | Everyone | Quick start (this file) |
| [README.jp.md](README.jp.md) | Everyone | Japanese documentation |
| [CHANGELOG.md](CHANGELOG.md) | Everyone | Version history |
| [CONTRIBUTING.md](CONTRIBUTING.md) | Contributors | Setup & contribution guide |
| [skills/SKILL.md](skills/SKILL.md) | Users | Full documentation |
| [skills/scripts/MetaGenerateExpression.md](skills/scripts/MetaGenerateExpression.md) | Users | Nano Banana Pro prompt generator |

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
