import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent.parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))


def t_utc(seconds: int = 0) -> datetime:
    """テスト共通の基準時刻（2026-05-26 12:00 UTC）＋ seconds。

    時刻依存テストで 7 ファイルに同一コピペされていた `_t()` の一本化。
    既存の呼び出し名は `from tests.conftest import t_utc as _t` で保てる。
    """
    base = datetime(2026, 5, 26, 12, 0, 0, tzinfo=timezone.utc)
    return base + timedelta(seconds=seconds)
