"""Entry point for ContextPreloader.

Usage:
  python -m scripts                          # Hook mode (global only)
  python -m scripts --profile weave          # Hook mode (global + profile)
  python -m scripts list                     # List sources
  python -m scripts add --path P --label L   # Add source
  python -m scripts remove --id ID           # Remove source
  python -m scripts test                     # Test sources
  python -m scripts profiles                 # List profiles
"""
from scripts.interfaces.cli import main

if __name__ == "__main__":
    main()
