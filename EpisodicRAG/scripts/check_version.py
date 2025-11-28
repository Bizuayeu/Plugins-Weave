#!/usr/bin/env python3
"""
バージョン整合性チェックスクリプト
==================================

以下の3箇所でバージョンが一致しているか検証します：
- scripts/domain/version.py (__version__) - Single Source of Truth
- .claude-plugin/plugin.json (version)
- pyproject.toml (version)

Usage:
    python scripts/check_version.py
"""

import json
import re
import sys
from pathlib import Path


def main() -> int:
    """バージョン整合性をチェックし、結果を返す"""
    # プラグインルートを取得
    script_dir = Path(__file__).parent
    plugin_root = script_dir.parent

    # 1. version.py から読み取り (SSoT)
    version_file = script_dir / "domain" / "version.py"
    try:
        version_content = version_file.read_text(encoding="utf-8")
        match = re.search(r'__version__\s*=\s*"([^"]+)"', version_content)
        ssot_version = match.group(1) if match else None
    except FileNotFoundError:
        print(f"ERROR: {version_file} not found")
        return 1

    if not ssot_version:
        print(f"ERROR: Could not parse __version__ from {version_file}")
        return 1

    # 2. plugin.json から読み取り
    plugin_json_path = plugin_root / ".claude-plugin" / "plugin.json"
    try:
        plugin_data = json.loads(plugin_json_path.read_text(encoding="utf-8"))
        plugin_version = plugin_data.get("version")
    except FileNotFoundError:
        print(f"ERROR: {plugin_json_path} not found")
        return 1
    except json.JSONDecodeError as e:
        print(f"ERROR: Invalid JSON in {plugin_json_path}: {e}")
        return 1

    # 3. pyproject.toml から読み取り
    pyproject_path = plugin_root / "pyproject.toml"
    try:
        pyproject_content = pyproject_path.read_text(encoding="utf-8")
        match = re.search(r'^version\s*=\s*"([^"]+)"', pyproject_content, re.MULTILINE)
        pyproject_version = match.group(1) if match else None
    except FileNotFoundError:
        print(f"ERROR: {pyproject_path} not found")
        return 1

    if not pyproject_version:
        print(f"ERROR: Could not parse version from {pyproject_path}")
        return 1

    # 比較
    all_match = ssot_version == plugin_version == pyproject_version

    print("Version Check Results:")
    print(f"  version.py (SSoT): {ssot_version}")
    print(f"  plugin.json:       {plugin_version}")
    print(f"  pyproject.toml:    {pyproject_version}")

    if all_match:
        print(f"\nAll versions match: {ssot_version}")
        return 0
    else:
        print("\nERROR: Version mismatch detected!")
        print("Please update all files to match version.py (Single Source of Truth)")
        return 1


if __name__ == "__main__":
    sys.exit(main())
