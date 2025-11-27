#!/usr/bin/env python3
"""
EpisodicRAG Interfaces Layer
============================

エントリーポイント・CLIスクリプト層。
application層に依存。

Scripts:
    - finalize_from_shadow: ShadowからRegularDigestを作成
    - save_provisional_digest: ProvisionalDigestを保存

Usage:
    python -m interfaces.finalize_from_shadow weekly "タイトル"
    python -m interfaces.save_provisional_digest weekly data.json
"""

from interfaces.finalize_from_shadow import DigestFinalizerFromShadow
from interfaces.save_provisional_digest import ProvisionalDigestSaver
from interfaces.interface_helpers import sanitize_filename, get_next_digest_number

__all__ = [
    "DigestFinalizerFromShadow",
    "ProvisionalDigestSaver",
    "sanitize_filename",
    "get_next_digest_number",
]
