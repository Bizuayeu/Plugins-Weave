# Contributing to EmailingEssay

Welcome! This guide helps you contribute to EmailingEssay.

## Table of Contents

- [Development Setup](#development-setup)
- [Project Structure](#project-structure)
- [Code Style](#code-style)
- [Testing](#testing)
- [Submitting Changes](#submitting-changes)
- [Extension Guide](#extension-guide)

---

## Development Setup

### Prerequisites

- Python 3.10+
- Git

### Installation

1. Fork and clone the repository
2. Install the package with its development dependencies, from the `EmailingEssay` directory:

   ```bash
   pip install -e ".[dev]"
   ```

3. Verify setup:

   ```bash
   python -m pytest
   ```

---

## Project Structure

```text
EmailingEssay/
├── commands/essay.md       # Command definition
├── agents/essay-writer.md  # Agent specification
├── …                       # Docs & manifests omitted
└── skills/
    ├── reflect/            # Reflection skill (agent-driven)
    │   └── SKILL.md
    └── send-email/         # Email sending skill
        ├── SKILL.md
        └── scripts/        # Python implementation: domain/ usecases/ adapters/ frameworks/ tests/
```

The full `scripts/` tree is kept in one place, `CLAUDE.md` → **File Structure**; for the layers, see
`CLAUDE.md` → **Clean Architecture Details**.

---

## Code Style

- **Python**: formatted with `ruff format` (line length 88) and linted with `ruff check`; the rules live in `pyproject.toml`
- **Type hints**: Required for public functions
- **Docstrings**: Triple-quoted, describe purpose
- **Naming**:
  - Classes: `PascalCase`
  - Functions/variables: `snake_case`
  - Constants: `UPPER_SNAKE_CASE`

---

## Testing

### Running Tests

Run from the `EmailingEssay` directory, as CI does:

```bash
python -m pytest                                          # All tests, with coverage
python -m pytest --no-cov skills/send-email/scripts/tests/domain/  # Domain layer only (coverage gate applies to full runs)
```

### Test Structure

Tests mirror the Clean Architecture layers:

- `tests/domain/` - Entity tests
- `tests/usecases/` - Business logic tests
- `tests/adapters/` - Adapter tests

### Available Fixtures (conftest.py)

| Fixture | Description |
|---------|-------------|
| `mock_mail_port` | Type-safe MailPort mock |
| `mock_scheduler_port` | SchedulerPort mock |
| `mock_schedule_storage` | ScheduleStoragePort mock |
| `mock_waiter_storage` | WaiterStoragePort mock |
| `mock_process_spawner` | ProcessSpawnerPort mock |
| `sample_schedule_dict` | Sample schedule data |

---

## Submitting Changes

1. Create a feature branch: `git checkout -b feature/your-feature`
2. Make changes with tests
3. Run full test suite: `pytest`
4. Update CHANGELOG.md for user-facing changes
5. Submit PR with clear description

### PR Checklist

- [ ] Tests pass
- [ ] New code has tests
- [ ] CHANGELOG.md updated (if applicable)
- [ ] No unrelated changes

---

## Extension Guide

### Adding a Mail Adapter

1. Create `adapters/mail/new_adapter.py`
2. Implement `MailPort` — its method signatures are defined in `usecases/ports.py`, the one place they are kept
3. Register in `usecases/factories.py`
4. Add tests in `tests/adapters/`

### Adding a Scheduler

1. Create `adapters/scheduler/new_scheduler.py`
2. Subclass `BaseSchedulerAdapter` (`adapters/scheduler/base.py`), which follows `SchedulerPort` in `usecases/ports.py`
3. Handle platform detection in `get_scheduler()` (`adapters/scheduler/__init__.py`)

---

**EmailingEssay** | [GitHub](https://github.com/Bizuayeu/Plugins-Weave)
