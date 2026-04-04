"""
module1/verify_setup.py
-----------------------
Pre-flight check for Module 1 — and every module after it.
Run this before starting any exercise:

    python module1/verify_setup.py

Checks Python version, ANTHROPIC_API_KEY, required packages, and the
optional GitHub CLI (gh) used in later modules.
"""

import sys
import os

# Delegate to the shared implementation so there is a single source of truth.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from shared.verify_setup import main  # noqa: E402

if __name__ == "__main__":
    main()
