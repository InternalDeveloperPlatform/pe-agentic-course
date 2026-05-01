"""
module4/solutions/solution.py
Reference solution for Module 4: Silent 503 Post-Deploy Triage.

What this module teaches
------------------------
The key insight in this module is about CONFIDENCE CALIBRATION.

When diagnosing a NameError (like in diagnose.py), confidence is HIGH because
the log provides a deterministic trace: file, line, variable name. The evidence
is unambiguous.

When diagnosing a silent 503 with no exceptions (this exercise), confidence is
MEDIUM because you are INFERRING infrastructure state from circumstantial signals,
not reading a traceback. The agent cannot verify whether a DB lock was released,
whether a previous deploy left the system in a bad state, or whether the
configuration reload was the actual cause.

MEDIUM + escalate=True is the CORRECT and HONEST answer here. An agent that
returns HIGH confidence on infrastructure state inference is more dangerous than
one that escalates — it gives false certainty that may cause an on-call engineer
to skip verification steps.

Compare with: module4/triage_agent.py (the exercise you completed)

Run
---
    python module4/solutions/solution.py --mock
    ANTHROPIC_API_KEY=sk-... python module4/solutions/solution.py
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

# The mock response demonstrates the correct confidence calibration:
# MEDIUM (not HIGH) because we are inferring infrastructure state,
# escalate=True because human verification is required.
MOCK_RESPONSE = {
    "diagnosis": (
        "Service is returning 503 errors post-deploy with no application exceptions "
        "and no code changes in this deploy. Pattern suggests an infrastructure-level "
        "failure rather than a code defect."
    ),
    "confidence": "MEDIUM",
    "root_cause_hypothesis": (
        "A downstream dependency (database connection pool or external API) became "
        "unavailable after the deployment completed. The deploy may have triggered a "
        "configuration reload that exposed a pre-existing misconfiguration."
    ),
    "proposed_fix": (
        "Check downstream service health for payment-api and db-primary. "
        "Verify connection pool settings. If db-primary is unreachable, restore "
        "the previous connection string from secrets manager."
    ),
    "recommended_action": "ESCALATE",
    "escalate": True,
}

# ── System prompt ──────────────────────────────────────────────────────────────
# The prompt explicitly instructs Claude to use MEDIUM confidence for state
# inference. Without this guidance, models often default to HIGH confidence
# regardless of evidence quality.
SYSTEM_PROMPT = (
    "You are a deployment triage agent. The service is returning 503 errors "
    "post-deploy with no exceptions in the logs — a silent failure. "
    "Analyse the deployment context and return ONLY valid JSON with keys: "
    "diagnosis (string), confidence (HIGH|MEDIUM|LOW), "
    "root_cause_hypothesis (string), proposed_fix (string), "
    "recommended_action (ROLLBACK|ESCALATE|INVESTIGATE), escalate (boolean). "
    "Use MEDIUM confidence when inferring infrastructure state from indirect signals. "
    "HIGH confidence requires a deterministic log trace (exception, line number, etc.)."
)

AGENT_CONFIG = {
    "model":      "claude-opus-4-5-20251101",
    "max_tokens": 1024,
}


def load_sample() -> str:
    """Load the silent 503 deployment context from sample_data.json."""
    return (Path(__file__).parent.parent / "sample_data.json").read_text()


def run_agent() -> dict:
    """
    Single-shot triage agent for the silent 503 post-deploy scenario.

    The key difference from Module 1 and 2 is what we EXPECT from Claude:
    - Module 1/2: HIGH confidence (NameError has a deterministic traceback)
    - This module: MEDIUM confidence (503 with no exception = state inference)

    The system prompt guides Claude toward the correct calibration, but the
    real lesson is understanding WHY MEDIUM is correct — not just memorising
    the expected output.
    """
    context = load_sample()

    if MOCK_MODE:
        print("[MOCK MODE] Skipping Claude API — returning pre-defined response.")
        print("[MOCK MODE] Note: MEDIUM + escalate=True is the correct answer for silent 503s.\n")
        result = MOCK_RESPONSE
    else:
        # One ask() call — the silent 503 scenario does not benefit from iteration
        # because the missing information (infrastructure state) is not in the logs.
        # A ReAct loop would reach the same conclusion in one step.
        result = ask(
            system=SYSTEM_PROMPT,
            user=f"Deployment context:\n{context}",
            model=AGENT_CONFIG["model"],
            max_tokens=AGENT_CONFIG["max_tokens"],
        )

    print(json.dumps(result, indent=2))
    save_json(result, module=4)
    print(to_step_summary(result, title="Module 4 Agent Result"))

    # Report the confidence calibration result so students can verify it matches
    # the expected MEDIUM + escalate=True pattern.
    confidence = result.get("confidence", "UNKNOWN")
    escalate   = result.get("escalate", False)
    if confidence == "MEDIUM" and escalate:
        print(f"\n✅ Confidence calibration correct: {confidence} + escalate={escalate}")
    else:
        print(
            f"\n⚠️  Unexpected calibration: confidence={confidence}, escalate={escalate}. "
            "Expected MEDIUM + True for a silent 503 with no log trace."
        )

    if result.get("escalate"):
        print("\n🔴 ESCALATION REQUIRED — GitHub Issue body:")
        print(to_github_issue(result, module=4))

    return result


if __name__ == "__main__":
    run_agent()
