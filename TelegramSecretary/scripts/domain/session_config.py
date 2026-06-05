"""session 総枠（継続時間）の値オブジェクト。0 < x ≤ 86400 を保証。"""
from __future__ import annotations

from dataclasses import dataclass

MIN_SECONDS = 1
MAX_SECONDS = 86400  # 24h（session_duration_sec の値域上限ガード。プラットフォームの実セッション上限＝実測 約4h は別レイヤー、SETUP.md / config.template.json 参照）


@dataclass(frozen=True)
class SessionDuration:
    """session の継続時間（秒）。`from_seconds` で範囲検証（MIN_SECONDS ≤ x ≤ MAX_SECONDS）。

    **`watch_window.WatchWindow` の「<=0 は無限窓」セマンティクスとは別物**——
    あちらは watch の 1 窓で 0/負＝無限。こちらは session 総枠であり 0/負は不正（ValueError）。
    範囲検証のみを責務とし、env / json / bootstrap には依存しない（純粋 Domain）。
    値の取得元（config.json）と「欠落＝必須エラー」の判断は Interface 層が担う。
    """

    seconds: int

    @classmethod
    def from_seconds(cls, value: int) -> "SessionDuration":
        """範囲内なら値オブジェクトを返し、範囲外（< MIN / > MAX）なら ValueError。"""
        if value < MIN_SECONDS or value > MAX_SECONDS:
            raise ValueError(
                f"session_duration_sec must be {MIN_SECONDS}..{MAX_SECONDS} seconds "
                f"(got {value}, max {MAX_SECONDS})"
            )
        return cls(seconds=value)
