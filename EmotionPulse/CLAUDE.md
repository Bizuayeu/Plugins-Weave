# EmotionPulse Development Guidelines

## Overview

Stop hookでメインエージェントに感情の自己評価を指示 → Pythonスクリプトで`emotion_state.json`書き出し → statusline表示。
感情の評価者はメインエージェント自身。ロックファイルで二重発火防止（ralph-loop準拠）。

## Setup

```
/EmotionPulse:setup
```

対話式でhook登録 + statusline設定 + display configを行う。

## Architecture

Clean Architecture 4層構造:

| Layer | Directory | Responsibility |
|-------|-----------|----------------|
| Domain | `scripts/domain/` | Models, constants (no I/O) |
| Infrastructure | `scripts/infrastructure/` | File I/O, config loading, path resolution |
| Application | `scripts/application/` | State management, formatting, hook config generation |
| Interfaces | `scripts/interfaces/` | Stop hook handler, emotion writer CLI, statusline |

## Data Flow

```
Stop hook (command型) → stop_hook_handler.py
  ロック確認:
    ロックあり（同session + 60秒以内）→ approve + ロック削除
    ロックなし or 期限切れ → block + ロック書き出し + systemMessage注入
      ↓
メインエージェント（自己評価）
  → python emotion_writer.py '{"calm":2,...}'
      ↓
emotion_writer.py → EmotionVector → atomic write → emotion_state.json
      ↓
statusline.py → emotion_state.json読み → emoji表示
```

## Development

```bash
cd plugins-weave/EmotionPulse

python -m pytest scripts/tests/ -v
python -m pytest scripts/tests/ -v --cov=scripts --cov-report=term-missing
python -m ruff check scripts/
python -m mypy scripts/
```
