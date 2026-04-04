"""
shared/verify_setup.py
----------------------
Pre-flight check for the course environment.
Run before any module exercise: python shared/verify_setup.py
"""

import sys
import os
import subprocess
import importlib.util


REQUIRED_PYTHON = (3, 10)
REQUIRED_PACKAGES = ["anthropic"]


def check_python():
    v = sys.version_info
    ok = v >= REQUIRED_PYTHON
    status = "✅" if ok else "❌"
    print(f"{status} Python {v.major}.{v.minor}.{v.micro}  (need ≥ {REQUIRED_PYTHON[0]}.{REQUIRED_PYTHON[1]})")
    return ok


def check_api_key():
    key = os.environ.get("ANTHROPIC_API_KEY", "")
    ok = bool(key and key.startswith("sk-"))
    status = "✅" if ok else "❌"
    hint = "" if ok else "  → Set with: export ANTHROPIC_API_KEY=your_key_here"
    print(f"{status} ANTHROPIC_API_KEY{hint}")
    return ok


def check_packages():
    all_ok = True
    for pkg in REQUIRED_PACKAGES:
        found = importlib.util.find_spec(pkg) is not None
        status = "✅" if found else "❌"
        hint = "" if found else f"  → Install with: pip install {pkg}"
        print(f"{status} {pkg}{hint}")
        all_ok = all_ok and found
    return all_ok


def check_gh_cli():
    try:
        result = subprocess.run(
            ["gh", "--version"],
            capture_output=True, text=True, timeout=5
        )
        ok = result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        ok = False
    status = "✅" if ok else "⚠️ "
    hint = "" if ok else " (optional — needed for GitHub Issue exercises)"
    print(f"{status} GitHub CLI (gh){hint}")
    return True  # Non-blocking — gh is optional for early modules


def main():
    print("=" * 50)
    print("  Agentic AI in Platform Engineering — Setup Check")
    print("=" * 50)
    results = [
        check_python(),
        check_api_key(),
        check_packages(),
        check_gh_cli(),
    ]
    print("=" * 50)
    if all(results):
        print("✅  All checks passed. You're ready to run the exercises.")
    else:
        print("❌  One or more checks failed. Fix the issues above and re-run.")
        sys.exit(1)


if __name__ == "__main__":
    main()
