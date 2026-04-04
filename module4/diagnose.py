"""
module4/diagnose.py
CI/CD Diagnostic Agent — reads a failure log and produces a structured diagnosis.

This is the DEMO agent shown in Module 4 slide 6 ("diagnose.py Architecture Deep Dive").
It accepts log input from three sources (in priority order):
  1. File argument:   python module4/diagnose.py --log /tmp/failure.log
  2. stdin:           cat failure.log | python module4/diagnose.py
  3. Built-in sample: python module4/diagnose.py   (uses module4/broken_app failure log)

MOCK MODE: python module4/diagnose.py --mock
"""

import os
import sys
import json
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from shared.claude_client import ask
from shared.output import save_json, to_step_summary, to_github_issue

# ── Mock mode ──────────────────────────────────────────────────────────────────
MOCK_MODE = "--mock" in sys.argv or os.environ.get("MOCK_MODE") == "1"

MOCK_RESPONSE = {
    "error_type": "NameError",
    "root_cause": "Two undefined variable references in broken_app/app.py. Bug 1 (line 37): 'statis' is referenced but never defined — likely a typo for a loop counter. Bug 2 (line 44): 'app_version' is used but the constant is named APP_VERSION (case mismatch).",
    "confidence": "HIGH",
    "fix": {
        "bug_1": {
            "file": "module4/broken_app/app.py",
            "line": 37,
            "original": "count += statis",
            "corrected": "count += 1  # increment the loop counter directly",
        },
        "bug_2": {
            "file": "module4/broken_app/app.py",
            "line": 44,
            "original": "version = app_version",
            "corrected": "version = APP_VERSION",
        },
    },
    "post_mortem": {
        "what_happened": "The CI pipeline failed with two NameErrors in broken_app/app.py, preventing the application from starting.",
        "why_it_happened": "A typo ('statis' instead of a defined counter) and a case error ('app_version' vs the constant 'APP_VERSION') were introduced in the same commit. These are syntax-level errors that Python raises at runtime, not compile time.",
        "how_to_prevent": "Add a pre-commit hook that runs `python -m py_compile` on all changed .py files. Enable a linter (ruff or pylint) in CI to catch NameErrors before they reach the test stage.",
    },
    "escalate": False,
}

# ── System prompt ──────────────────────────────────────────────────────────────
SYSTEM_PROMPT = """\
You are a CI/CD pipeline triage agent. You receive the failure log from a GitHub Actions run.

Analyse the log and return ONLY valid JSON with these keys:
- error_type (string): the Python exception class, e.g. "NameError", "ImportError", "AssertionError"
- root_cause (string): a one-paragraph plain-English explanation of what went wrong and why
- confidence (HIGH|MEDIUM|LOW): HIGH for deterministic errors (NameError, SyntaxError), MEDIUM for state-inference, LOW for unknown
- fix (object): for each bug found, include { file, line, original, corrected } — include the exact corrected code snippet
- post_mortem (object): { what_happened, why_it_happened, how_to_prevent } — one sentence each
- escalate (boolean): true only if human intervention is required before the fix can be applied

Rules:
- Include the exact line number and code snippet for every fix you suggest.
- If there are multiple bugs, list all of them in the fix object.
- Keep post_mortem sentences concise — each should be one sentence only.
- For NameErrors and SyntaxErrors, confidence is always HIGH.
"""

# ── Built-in sample log from running broken_app/app.py ────────────────────────
SAMPLE_LOG = """\
2026-04-03T09:15:00 [INFO] === broken_app starting ===
Traceback (most recent call last):
  File "module4/broken_app/app.py", line 62, in <module>
    total = process_requests(sample_requests)
  File "module4/broken_app/app.py", line 37, in process_requests
    count += statis          # Bug 1: NameError — 'statis' is not defined
NameError: name 'statis' is not defined
"""


def load_log(args) -> str:
    """Load failure log from file argument, stdin, or built-in sample."""
    if args.log:
        log_path = Path(args.log)
        if not log_path.exists():
            print(f"[ERROR] Log file not found: {args.log}", file=sys.stderr)
            sys.exit(1)
        print(f"[diagnose] Reading log from: {args.log}")
        return log_path.read_text()

    if not sys.stdin.isatty():
        print("[diagnose] Reading log from stdin...")
        return sys.stdin.read()

    print("[diagnose] No log source provided — using built-in broken_app sample log")
    return SAMPLE_LOG


def run_agent(log_content: str) -> dict:
    user_message = f"CI failure log:\n\n{log_content}"

    if MOCK_MODE:
        print("[MOCK MODE] Skipping Claude API — returning pre-defined diagnosis.\n")
        return MOCK_RESPONSE

    return ask(
        system=SYSTEM_PROMPT,
        user=user_message,
        max_tokens=2048,
    )


def main():
    parser = argparse.ArgumentParser(description="Module 4 CI/CD Diagnostic Agent")
    parser.add_argument("--log", help="Path to the failure log file")
    parser.add_argument("--mock", action="store_true", help="Run in mock mode (no API call)")
    args = parser.parse_args()

    log_content = load_log(args)

    # Trim log to last 8,000 characters — full logs can be 100k+
    if len(log_content) > 8000:
        log_content = "...[trimmed]...\n" + log_content[-8000:]
        print(f"[diagnose] Log trimmed to last 8,000 characters")

    print("\n[diagnose] Running diagnosis...\n")
    result = run_agent(log_content)

    print(json.dumps(result, indent=2))
    save_json(result, module=4, label="diagnosis")
    print(to_step_summary(result, title="Module 4 Diagnosis Result"))

    if result.get("escalate"):
        print("\n🔴 ESCALATION REQUIRED — creating GitHub Issue body:")
        print(to_github_issue(result, module=4))
    else:
        print("\n✅ No escalation — agent produced a self-contained fix")

    return result


if __name__ == "__main__":
    main()
