"""UseCase 層のセキュリティ観測ログ（stderr へ 1 行、本文は載せない）。

未認可アクセス・レート超過・出力の redact は「起きたことが痕跡を残さなければ観測できない」
（ops-rules §1「ログを残す」）。一方 stdout は emitter の JSON Lines 専用チャネルなので、
観測ログは stderr にしか出せない。

I/O を伴うため本来は Adapter 層の役目だが、`usecases/outbound.py` の `validate_attachments`
（決定論的 FS I/O を UseCase に置く既存判断）と同じ線引きでここに置く——Port を 1 本増やして
全 UseCase の構築点に logger を配線するより、決定論的な 1 行出力として閉じ込める方が薄い。
書式は Adapter 側の `log_media_failure`（`[tag] ...`）に揃える。
"""

from __future__ import annotations

import sys


def log_security_event(event: str, **fields: object) -> None:
    """`[security] <event> k=v ...` を stderr に 1 行出す。

    fields には識別子・時刻・件数のみを渡す契約（受信本文・秘匿値そのものは渡さない）。
    """
    detail = " ".join(f"{key}={value}" for key, value in fields.items())
    print(f"[security] {event} {detail}".rstrip(), file=sys.stderr)
