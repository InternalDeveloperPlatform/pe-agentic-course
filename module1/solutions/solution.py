"""
module1/solutions/solution.py
Reference solution for Module 1: Hello Agent — first Claude API call.

What this module teaches
------------------------
The simplest possible agent pattern: load a log file, send it to Claude with
a structured system prompt, parse the JSON response, and save the output.
No loops, no tools, no history — just the core call-and-parse pattern that
every subsequent module builds on.

Compare with: module1/agent.py (the exercise file you completed)

Run
---
    python module1/solutions/solution.py --mock     # no API key needed
    ANTHROPIC_API_KEY=sk-... python module1/solutions/solution.py
"""

import os
import sys
import json
from pathlib import Path

# ── Path setup ─────────────────────────────────────────────────────────────────
# solutions/ is one level deeper than the module root, so we go up two levels
# to reach the repo root where shared/ lives.
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from shared.claude_client import ask
from shared.output import save_json, to_step_summary, to_github_issue

# ── Mock mode ──────────────────────────────────────────────────────────────────
MOCK_MODE = "--mock" in sys.argv or os.environ.get("MOCK_MODE") == "1"

# Pre-baked response that matches what Claude produces for sample_log.txt.
# In mock mode this is returned directly without calling the API.
MOCK_RESPONSE = {
    "summary": (
        "The Node.js test suite failed with 3 assertion errors in auth.test.js. "
        "Memory usage climbed to 87% during the run."
    ),
    "likely_cause": (
        "Uncleaned test fixtures are retaining references between test cases, "
        "causing heap growth and eventual assertion failures."
    ),
    "next_step": (
        "Add explicit cleanup in the afterEach hook for auth.test.js and reduce "
        "the fixture dataset size from 10,000 to 100 records for unit tests."
    ),
}

# ── System prompt ──────────────────────────────────────────────────────────────
# The system prompt is the "program" you give the model. It defines:
#   - Claude's role ("platform engineering assistant")
#   - The output CONTRACT: exactly which JSON keys are required and their types
# Keeping the contract in the system prompt (not the user message) means it
# applies to every call, even if the user message changes.
SYSTEM_PROMPT = (
    "You are a platform engineering assistant. "
    "Analyse the log snippet and return ONLY valid JSON with keys: "
    "summary (string), likely_cause (string), next_step (string)."
)


def load_sample() -> str:
    """Load the CI failure log from sample_log.txt (sibling of the module root)."""
    return (Path(__file__).parent.parent / "sample_log.txt").read_text()


def run_agent() -> dict:
    """
    Single-shot agent: send the log to Claude, return the parsed JSON result.

    This is the simplest form of an agent — one prompt, one response, done.
    No retry logic, no tools, no iteration. The right starting point for
    understanding the ask() / parse / save pattern.
    """
    log = load_sample()

    if MOCK_MODE:
        print("[MOCK MODE] Skipping Claude API — returning pre-defined response.")
        print("[MOCK MODE] Set ANTHROPIC_API_KEY and remove --mock to call the real API.\n")
        result = MOCK_RESPONSE
    else:
        # ask() calls the Claude API, parses the JSON response, and returns a dict.
        # system= sets the role and output contract.
        # user=   provides the data the agent should reason over.
        result = ask(
            system=SYSTEM_PROMPT,
            user=f"Log:\n{log}",
            max_tokens=512,
        )

    # Print the structured result to the terminal
    print(json.dumps(result, indent=2))

    # Write output/output_module1.json — picked up by GitHub Actions as an artifact
    save_json(result, module=1)

    # Emit a GitHub Actions Step Summary (visible in the Actions UI)
    print(to_step_summary(result, title="Module 1 Agent Result"))

    # Escalation path: if the agent decides a human must be paged, print the
    # GitHub Issue body so it can be copy-pasted or posted via the GitHub API.
    if result.get("escalate"):
        print("\n🔴 ESCALATION REQUIRED — GitHub Issue body:")
        print(to_github_issue(result, module=1))
    else:
        print("\n✅ No escalation — agent produced a self-contained response")

    return result


if __name__ == "__main__":
    run_agent()
