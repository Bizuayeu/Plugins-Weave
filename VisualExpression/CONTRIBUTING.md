# Contributing to VisualExpression

Thank you for your interest in contributing to VisualExpression!

## Prerequisites

- Python 3.8+
- Pillow library (`pip install Pillow`)

## Project Structure

```
VisualExpression/
├── README.md                    # Quick start guide (English)
├── README.jp.md                 # Quick start guide (Japanese)
├── CHANGELOG.md                 # Version history
├── CONTRIBUTING.md              # This file
├── .claude-plugin/
│   └── plugin.json              # Claude Code plugin metadata
└── skills/
    ├── SKILL.md                 # Full documentation
    ├── ExpressionImages.json    # Base64 encoded images (generated)
    ├── VisualExpressionUI.html  # Self-contained UI (generated)
    ├── VisualExpressionUI.template.html
    └── scripts/
        ├── MetaGenerateExpression.md
        └── MakeExpressionJson/  # Python pipeline
            ├── main.py          # CLI entry point
            ├── domain/          # Business logic
            │   ├── constants.py # Expression codes & config
            │   └── models.py    # Data models
            ├── usecases/        # Application logic
            │   ├── image_splitter.py
            │   ├── base64_encoder.py
            │   └── html_builder.py
            ├── adapters/        # I/O interfaces
            │   ├── file_handler.py
            │   └── zip_packager.py
            └── tests/           # Unit tests
```

## Architecture

MakeExpressionJson follows **Clean Architecture** principles:

- **domain/**: Core business rules and entities (no external dependencies)
- **usecases/**: Application-specific business rules
- **adapters/**: Interface adapters for external systems (file I/O, ZIP)

## Development Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/Bizuayeu/Plugins-Weave.git
   cd Plugins-Weave/VisualExpression
   ```

2. Install dependencies:
   ```bash
   pip install Pillow
   ```

3. Run tests:
   ```bash
   cd skills/scripts/MakeExpressionJson
   python -m pytest tests/
   ```

## Build Pipeline

The MakeExpressionJson pipeline processes images in this order:

1. **Split**: Grid image (1400×1120px) → 20 individual expressions (280×280px)
2. **Encode**: Convert each image to Base64 JPEG
3. **Build**: Inject Base64 data into HTML template
4. **Package**: Create ZIP for distribution (optional)

```
your_grid.png
    ↓
[split] → 20 individual images (280×280px)
    ↓
[encode] → ExpressionImages.json (Base64)
    ↓
[build] → VisualExpressionUI.html (template + JSON)
    ↓
[package] → VisualExpressionSkills.zip (optional)
```

## How to Contribute

### Reporting Issues

- Use GitHub Issues for bug reports and feature requests
- Include reproduction steps for bugs
- Describe expected vs actual behavior

### Pull Requests

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/your-feature`)
3. Make your changes
4. Run tests to ensure nothing is broken
5. Commit with clear messages
6. Push and create a Pull Request

### Code Style

- Follow PEP 8 for Python code
- Use type hints for function signatures
- Write docstrings for classes and public methods
- Keep functions small and focused

### Testing

- Add tests for new functionality
- Ensure existing tests pass before submitting PR
- Tests are located in `skills/scripts/MakeExpressionJson/tests/`

## License

By contributing, you agree that your contributions will be licensed under the same license as the project.

---

**VisualExpression** | [GitHub](https://github.com/Bizuayeu/Plugins-Weave)
