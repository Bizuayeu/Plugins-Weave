---
name: telegram-secretary
description: Cloud Routine 常駐 Telegram 秘書の登録・設定・管理表操作の入口（仕様 SSoT は skills/telegram-secretary/SKILL.md）
---

# /telegram-secretary — Cloud Routine 常駐 Telegram 秘書

Cloud Routine 上に常駐する Telegram 秘書の **登録・設定・管理表操作の入口**。仕様の SSoT は [`skills/telegram-secretary/SKILL.md`](../skills/telegram-secretary/SKILL.md)、Cloud Routine 起動手順は [`ROUTINE_PROMPT.md`](../ROUTINE_PROMPT.md)。

## Architecture

- **応答主体は親エージェント**（SecretaryRole を被る）。本スキルは fetch / 認可 / 正規化 / 送信のみを担い、LLM 推論をサブプロセスに投げない（設計原則）。
- **二系統**: 決定論 CLI（`scripts/main.py` の subcommand）と Cloud Routine ライフサイクル（`RemoteTrigger` ツール手順）。前者は設定・管理表・疎通、後者は schedule / unschedule。

## Subcommands

| Subcommand | 機能 | 実体 |
|---|---|---|
| `schedule` | Cloud Routine への登録 / 有効化 / 設定上書き（upsert） | `RemoteTrigger` 手順（[ROUTINE_PROMPT.md](../ROUTINE_PROMPT.md)「Cloud Routine ライフサイクル管理」節）＋ `init-config` |
| `unschedule` | 停止（`enabled:false`、二度と起動しない） | `RemoteTrigger update` |
| `init-config` / `show-config` / `validate-config` | 運用設定（config.json）の生成・表示・検証 | `scripts/main.py` |
| `individuals\|tasks\|knowledge {list\|get\|add\|remove}` | 管理表 CRUD（何を残すかは SecretaryRole 判断、書き込みは決定論 I/O） | `scripts/main.py` |
| `test --chat-id` | owner chat への疎通 ping | `scripts/main.py test` |

> 詳細な引数・exit code・env vars は [`SKILL.md`](../skills/telegram-secretary/SKILL.md) の Subcommands 表が SSoT。

## Usage

```bash
# Cloud Routine に登録（勤務帯 cron + config.json の session_duration_sec）
/telegram-secretary schedule

# 停止（state・config は消さない＝再 schedule で即復帰）
/telegram-secretary unschedule

# 運用設定の生成・確認
/telegram-secretary init-config --session-duration-sec 7200 --agent-name YourSecretary
/telegram-secretary show-config

# 管理表（関係者・依頼・対応知）
/telegram-secretary individuals list
/telegram-secretary tasks add --json '{...}'
/telegram-secretary knowledge get --key <uuid>

# 疎通テスト
/telegram-secretary test --chat-id <your-chat-id>
```

## 参照

- **はじめての方へ（セットアップ手順書）**: [`SETUP.md`](../SETUP.md)
- 仕様 SSoT: [`skills/telegram-secretary/SKILL.md`](../skills/telegram-secretary/SKILL.md)
- Cloud Routine 実行手順: [`ROUTINE_PROMPT.md`](../ROUTINE_PROMPT.md)
- 設計正典: [`DESIGN.md`](../DESIGN.md) / 構造地図: [`STRUCTURE.md`](../STRUCTURE.md) / セキュリティ正典: [`SECURITY.md`](../SECURITY.md)

---

**TelegramSecretary** | [GitHub](https://github.com/Bizuayeu/Plugins-Weave)
