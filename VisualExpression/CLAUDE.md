# VisualExpression Development Guidelines

## Overview

VisualExpression is a visual expression system for AI personas with emotion-based face switching.
This document provides development guidelines specific to this project.

---

## Design Philosophy

### Architecture

- **Clean Architecture**: domain/usecases/adapters separation
  - `domain/`: Core business rules (no external dependencies)
  - `usecases/`: Application-specific logic
  - `adapters/`: Interface adapters for I/O (file, ZIP)

### Documentation

- **Single Source of Truth**: [skills/SKILL.md](skills/SKILL.md) is the canonical specification
- **Bilingual Support**: Maintain English and Japanese versions in parallel

### Development Approach

- **Test-Driven**: Write tests before implementation
- **Incremental Progress**: Small, compilable changes
- **Simplicity**: Avoid premature abstractions

---

## Coding Standards

### Python

- **Style**: PEP 8 compliant
- **Type Hints**: Required for all function signatures
- **Docstrings**: Required for classes and public methods
- **Functions**: Small and focused (single responsibility)

### Testing

- **Framework**: pytest
- **Coverage**: Maintain 90%+ code coverage
- **Test Cases**: 209 test cases across 19 test files
- **Pre-commit**: Run `python -m pytest tests/` before committing

```bash
cd skills/scripts/MakeExpressionJson
python -m pytest tests/ -v
```

---

## Specification References

| Topic | Reference |
|-------|-----------|
| Expression Codes (20 types) | [skills/SKILL.md#expression-codes](skills/SKILL.md#expression-codes) |
| Grid Specifications | [skills/SKILL.md#technical-details](skills/SKILL.md#technical-details) |
| Build Pipeline | [CONTRIBUTING.md#build-pipeline](CONTRIBUTING.md#build-pipeline) |
| Troubleshooting | [skills/SKILL.md#troubleshooting](skills/SKILL.md#troubleshooting) |

---

## Quick Reference

### Image Specifications

- Grid: 1400x1120px (4 rows x 5 columns)
- Cell: 280x280px per expression
- Format: JPEG (Base64 encoded)

### Expression Categories

| Category | Codes |
|----------|-------|
| Basic | normal, smile, focus, diverge |
| Emotion | joy, elation, surprise, calm |
| Negative | anger, sadness, rage, disgust |
| Anxiety | anxiety, fear, upset, worry |
| Special | sleepy, cynical, defeated, dreamy |

---

## Important Notes

- **Do not duplicate specifications**: Always reference SKILL.md
- **Update both language versions**: When editing README.md or MetaGenerateExpression.md
- **Run tests before PR**: All 209 test cases must pass

---

**VisualExpression** | [GitHub](https://github.com/Bizuayeu/Plugins-Weave)
