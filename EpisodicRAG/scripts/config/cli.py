#!/usr/bin/env python3
"""
Config CLI
==========

設定管理のCLIエントリーポイント。

Usage:
    python -m config.cli --show-paths
    python -m config.cli --plugin-root /path/to/plugin
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Optional


def main(plugin_root: Optional[Path] = None) -> None:
    """
    CLI エントリーポイント

    Args:
        plugin_root: Pluginルート（テスト用にオーバーライド可能）
    """
    # 循環インポートを避けるため、関数内でインポート
    from . import DigestConfig

    parser = argparse.ArgumentParser(description="Digest Plugin Configuration Manager")
    parser.add_argument("--show-paths", action="store_true", help="Show all configured paths")
    parser.add_argument("--plugin-root", type=Path, help="Override plugin root")

    args = parser.parse_args()

    # 引数またはテスト用のplugin_rootを使用
    effective_root = args.plugin_root if args.plugin_root else plugin_root

    try:
        config = DigestConfig(plugin_root=effective_root)

        if args.show_paths:
            config.show_paths()
        else:
            # デフォルト: JSON出力
            print(json.dumps(config.config, indent=2, ensure_ascii=False))

    except (FileNotFoundError, Exception) as e:
        # ConfigError やその他のエラーをキャッチ
        from .exceptions import ConfigError
        if isinstance(e, (FileNotFoundError, ConfigError)):
            sys.stderr.write(f"[ERROR] {e}\n")
            sys.exit(1)
        raise


if __name__ == "__main__":
    main()
