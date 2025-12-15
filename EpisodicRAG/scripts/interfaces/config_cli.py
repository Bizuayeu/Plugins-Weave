#!/usr/bin/env python3
"""
Config CLI
==========

設定管理のCLIエントリーポイント。

Usage:
    python -m interfaces.config_cli --show-paths
"""

import argparse
import json
import sys


def main() -> None:
    """CLI エントリーポイント"""
    # 循環インポートを避けるため、関数内でインポート
    from application.config import DigestConfig
    from domain.exceptions import ConfigError

    parser = argparse.ArgumentParser(description="Digest Plugin Configuration Manager")
    parser.add_argument("--show-paths", action="store_true", help="Show all configured paths")

    args = parser.parse_args()

    try:
        config = DigestConfig()

        if args.show_paths:
            config.show_paths()
        else:
            # デフォルト: JSON出力
            print(json.dumps(config.config, indent=2, ensure_ascii=False))

    except (FileNotFoundError, ConfigError) as e:
        sys.stderr.write(f"[ERROR] {e}\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
