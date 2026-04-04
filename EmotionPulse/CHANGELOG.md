# Changelog

## [1.2.0] - 2026-04-04

### Changed

- Stop hook → メインエージェント自己評価アーキテクチャに移行
- command型Stop hookがsystemMessageで自己評価を指示
- ロックファイルによる二重発火防止（ralph-loop準拠）

### Added

- `/EmotionPulse:setup` — 対話式セットアップコマンド
- `domain/models.py`: HookLock（ロック状態管理）
- `interfaces/stop_hook_handler.py` — ロックベースblock/approve制御
- `interfaces/emotion_writer.py` — CLI引数→バリデーション→状態書き出し
- `hooks/stop_handler.py` — thin launcher
- `application/hook_config.py` — Stop hook設定エントリ生成
- `domain/constants.py`: LOCK_FILENAME, LOCK_MAX_AGE_SECONDS

## [1.1.0] - 2026-04-04

### Changed

- TaskCompleted hookアーキテクチャ（実験、後に廃止）

## [1.0.0] - 2026-04-04

### Added

- Initial release (Stop hook + claude -p)
