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
2. Install dependencies:
   ```bash
   pip install yagmail pytest
   ```
3. Verify setup:
   ```bash
   cd skills/send-email/scripts
   pytest
   ```

---

## Project Structure

```text
EmailingEssay/
├── commands/essay.md       # Command definition
├── agents/essay-writer.md  # Agent specification
└── skills/
    ├── reflect/            # Reflection skill (agent-driven)
    │   └── SKILL.md
    └── send-email/         # Email sending skill
        ├── SKILL.md
        └── scripts/        # Python implementation
            ├── domain/    # Core entities
            ├── usecases/  # Business logic
            ├── adapters/  # External interfaces
            ├── frameworks/# Templates, logging
            └── tests/     # Test suite
```

For detailed architecture, see `CLAUDE.md` → **Clean Architecture Details** section.

---

## Code Style

- **Python**: PEP 8, 100 char line limit
- **Type hints**: Required for public functions
- **Docstrings**: Triple-quoted, describe purpose
- **Naming**:
  - Classes: `PascalCase`
  - Functions/variables: `snake_case`
  - Constants: `UPPER_SNAKE_CASE`

---

## Testing

### Running Tests

```bash
cd skills/send-email/scripts
pytest                    # All tests
pytest tests/domain/      # Domain layer only
pytest -v                 # Verbose output
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
2. Implement `MailPort` from `usecases/ports.py`:
   ```python
   from usecases.ports import MailPort

   class NewMailAdapter(MailPort):
       def send(self, to: str, subject: str, body: str) -> None:
           # Implementation
           pass

       def test(self) -> None:
           # Send test email
           pass

       def send_custom(self, subject: str, content: str) -> None:
           # Custom content
           pass
   ```
3. Register in `usecases/factories.py`
4. Add tests in `tests/adapters/`

### Adding a Scheduler

1. Create `adapters/scheduler/new_scheduler.py`
2. Implement `SchedulerPort`:
   ```python
   from usecases.ports import SchedulerPort, TaskInfo

   class NewSchedulerAdapter(SchedulerPort):
       def add(self, task_name: str, command: str, frequency: str, time: str, *, weekday: str = "", day_spec: str = "") -> None:
           pass

       def remove(self, name: str) -> None:
           pass

       def list(self) -> list[TaskInfo]:
           return []
   ```
3. Handle platform detection in factories

---

**EmailingEssay** | [GitHub](https://github.com/Bizuayeu/Plugins-Weave)
