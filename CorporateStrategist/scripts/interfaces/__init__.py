# CorporateStrategist CLI Interfaces
"""
CLI commands for CorporateStrategist plugin.

Usage:
    python -m scripts.interfaces.qcd_analyzer --help
    python -m scripts.interfaces.iching_divination --help
    python -m scripts.interfaces.fortune_teller_assessment --help
"""

from pathlib import Path

INTERFACES_DIR = Path(__file__).parent
SCRIPTS_DIR = INTERFACES_DIR.parent
PLUGIN_ROOT = SCRIPTS_DIR.parent
