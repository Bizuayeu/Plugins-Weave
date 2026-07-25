"""pytest bootstrap: put wakeup/scripts on sys.path so `import domain...` resolves.

Mirrors EmailingEssay's skills/<name>/scripts/ layout (scripts dir is the import root),
combined with ContextPreloader's frozen-dataclass + unittest/pytest conventions.
"""

import os
import sys

# conftest.py lives in scripts/tests/ -> parent of parent is scripts/
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
