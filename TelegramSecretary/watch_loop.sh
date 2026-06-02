#!/usr/bin/env bash
# watch ループの薄いラッパー。Cloud Routine の Monitor が消費する JSON Lines を stdout に流す。
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

exec python scripts/main.py watch "$@"
