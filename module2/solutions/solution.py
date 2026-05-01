"""
module2/solutions/solution.py
Reference solution for Module 2: Five-Step Agentic Loop.

What this module teaches
------------------------
Breaking a single agent call into five explicit, testable steps:
  1. write_prompt   — build the system prompt and user message
  2. call_api       — call Claude (or return mock)
  3. parse_json     — validate required keys are present
  4. execute_action — act on the result (print recommendation, escalate if needed)
  5. verify_result  — confirm the output meets success criteria

Why five steps instead of one?
Each step can be unit-tested independently. step3_parse_json() doesn't need the
API; step2_call_api() can be mocked without touching the prompt logic. This
decomposition is the foundation for every agent pipeline in the rest of the course.

Compare with: module2/triage_agent.py (the exercise you completed)
The exercise asks for a single run_agent() function. This solution shows how
the same logic can be organised into clearly-separated, independently-testable steps.

Run
---
    python module2/solutions/solution.py --mock
    ANTHROPIC_API_KEY=sk-... python module2/solutions/solution.py
"""

import os
import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from shared.claude_client import ask
from shared.output import save_json, to_step_summary, to_github_issue

# ── Mock mode ──────────────────────────────────────────────────────────────────
MOCK_MODE = "--mock" in sys.argv or os.environ.get("MOCK_MODE") == "1"

# Note: the exercise (triage_agent.py) returns summary/likely_cause/next_step.
# This solution uses a different output contract (diagnosis/recommended_action)
# to match the five-step structured pattern described in the README.
# Both are valid — the system prompt defines the contract; the agent returns it.
MOCK_RESPONSE = {
    "diagnosis": (
        "The deployment failed due to a missing environment variable "
        "PAYMENT_API_KEY in the production environment."
    ),
    "confidence": "HIGH",
    "recommended_action": (
        "Add PAYMENT_API_KEY to GitHub Actions secrets and reference it "
        "in the workflow env block."
    ),
    "escalate": False,
}

# ── System prompt ──────────────────────────────────────────────────────────────
# This prompt defines a tighter output schema than the exercise file,
# adding a confidence field and a boolean escalate gate.
SYSTEM_PROMPT = (
    "You are a CI/CD diagnostic agent. Analyse the build log and return ONLY valid JSON "
    "with keys: diagnosis (string), confidence (HIGH|MEDIUM|LOW), "
    "recommended_action (string), escalate (boolean). "
    "confidence is HIGH only when the root cause is directly visible in the log. "
    "Use MEDIUM when inferring state, LOW when the log is ambiguous."
)


# ── Five-step functions ────────────────────────────────────────────────────────

def step1_write_prompt(log: str) -> tuple:
    """
    Step 1 — Write the prompt.

    Separating prompt construction from the API call means you can unit-test
    the prompt independently (e.g. verify the user message contains key fields)
    without making any API call.

    Returns a (system_prompt, user_message) tuple.
    """
    user_msg = (
        f"Build log:\n{log}\n\n"
        "Diagnose the failure. Identify root cause, confidence level, and recommended action."
    )
    return SYSTEM_PROMPT, user_msg


def step2_call_api(system: str, user: str) -> dict:
    """
    Step 2 — Call the Claude API (or return mock).

    Isolating the API call lets you mock this step in tests without touching
    any of the prompt or action logic.
    """
    if MOCK_MODE:
        print("[MOCK MODE] Skipping Claude API — returning pre-defined response.\n")
        return MOCK_RESPONSE
    return ask(system=system, user=user, max_tokens=1024)


def step3_parse_json(result: dict) -> dict:
    """
    Step 3 — Validate the JSON response.

    Raises ValueError if any required key is missing. This is the contract
    enforcement step — if Claude returns an unexpected schema, fail here
    rather than silently passing bad data to the action step.
    """
    required = {"diagnosis", "confidence", "recommended_action", "escalate"}
    missing = required - set(result.keys())
    if missing:
        raise ValueError(
            f"Agent response missing required keys: {missing}\n"
            f"Got: {list(result.keys())}"
        )
    valid_confidence = {"HIGH", "MEDIUM", "LOW"}
    if result["confidence"] not in valid_confidence:
        raise ValueError(
            f"Invalid confidence value '{result['confidence']}'. "
            f"Expected one of {valid_confidence}."
        )
    return result


def step4_execute_action(result: dict) -> None:
    """
    Step 4 — Execute the recommended action.

    In a real system this step would call the GitHub API, send a Slack message,
    trigger a rollback, or open a PagerDuty incident. Here we print the action
    and escalation notice so you can see what an agent would do.
    """
    print(f"\n[ACTION] Confidence     : {result['confidence']}")
    print(f"[ACTION] Recommendation : {result['recommended_action']}")

    if result.get("escalate"):
        print("[ACTION] 🔴 ESCALATION REQUIRED")
        print(to_github_issue(result, module=2))
    else:
        print("[ACTION] ✅ No escalation — agent handled autonomously")


def step5_verify_result(result: dict) -> bool:
    """
    Step 5 — Verify the result meets success criteria.

    Returns True if the output is well-formed and actionable.
    In a production agent this might gate whether to proceed with an auto-fix
    or to fall back to human review.
    """
    has_valid_confidence = result.get("confidence") in ("HIGH", "MEDIUM", "LOW")
    has_recommendation = bool(result.get("recommended_action"))
    return has_valid_confidence and has_recommendation


def run() -> dict:
    """Orchestrate all five steps end to end."""
    log = (Path(__file__).parent.parent / "sample_log.txt").read_text()

    # Each step is a separate, testable function
    system, user   = step1_write_prompt(log)
    raw_result     = step2_call_api(system, user)
    result         = step3_parse_json(raw_result)
    step4_execute_action(result)
    success        = step5_verify_result(result)

    print(json.dumps(result, indent=2))
    save_json(result, module=2)
    print(to_step_summary(result, title="Module 2 Agent Result"))
    print(f"\n[VERIFY] All checks passed: {success}")
    return result


if __name__ == "__main__":
    run()
