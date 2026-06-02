"""CLI 終了コードの SSoT（Single Source of Truth）。

main.py と registry_cli.py が各々で定義/裸書きしていた終了コードをここに一本化する。
**これらの値は外部契約**: SKILL.md / ROUTINE_PROMPT.md / SECURITY.md が 0/1/2/3/4 を
公開仕様として明記し、bootstrap.sh / watch_loop.sh が分岐に使う。値は変更しない。

main.py は後方互換のためここから re-export する（既存テスト・docs の
`from main import EXIT_*` を割らない）。
"""
from __future__ import annotations

EXIT_OK = 0  # 正常終了
EXIT_FETCH_FAILED = 1  # getUpdates / send の一時的失敗（transient、リトライ可）
EXIT_CONFIG_INVALID = 2  # env/設定/入力が不正（fail-fast、リトライ不可）
EXIT_AUTH_FAILED = 3  # Telegram 認証失敗（401、bot_token 不正）
EXIT_LEASE_CONFLICT = 4  # lease 競合/喪失（並走奪取の自己治癒経路）
