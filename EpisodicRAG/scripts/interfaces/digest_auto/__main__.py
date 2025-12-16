#!/usr/bin/env python3
"""
Digest Auto CLI Entry Point
===========================

python -m interfaces.digest_auto で実行可能にする。
"""

import io
import sys

from . import main

if __name__ == "__main__":
    # Windows UTF-8入出力対応
    if sys.platform == "win32":
        sys.stdin = io.TextIOWrapper(sys.stdin.buffer, encoding="utf-8")
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

    main()
