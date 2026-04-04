"""
module4/triage_agent.py
Entry point for Module 4 exercise: Event-driven agent — diagnose a silent 503 failure and propose a fix

MOCK MODE
---------
Run without an API key to see the expected output format:
    python module4/triage_agent.py --mock
    MOCK_MODE=1 python module4/triage_agent.py

The mock response demonstrates the key teaching point of this module:
MEDIUM confidence + escalate=true is the CORRECT answer for a silent 503 with
no exceptions — state inference warrants caution, not high confidence.
"""

import os
import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from shared.claude_client import ask
from shared.output import save_json, to_step_summary, to_github_issue

# ── Mock mode flag ─────────────────────────────────────────────────────────────
MOCK_MODE = "--mock" in sys.argv or os.environ.get("MOCK_MODE") == "1"

# Key teaching point: MEDIUM + escalate=true for silent failures with state inference
MOCK_RESPONSE = {
    "diagnosis": "Service is returning 503 errors with no application exceptions, no code changes in this deploy. The pattern suggests an infrastructure-level issue rather than a code defect.",
    "confidence": "MEDIUM",
    "root_cause_hypothesis": "A downstream dependency (database connection pool or external API) became unavailable after deployment completed. The deployment may have triggered a configuration reload that exposed a pre-existing misconfiguration.",
    "proposed_fix": "Check downstream service health for payment-api and db-primary. Verify connection pool settings were not modified by the deployment. If db-primary is unreachable, restore the previous connection string from secrets manager.",
    "recommended_action": "ESCALATE",
    "escalate": True,
}

# ── Prompt & config ────────────────────────────────────────────────────────────
SYSTEM_PROMPT = (
    "You are a deployment triage agent. The service is returning 503 errors with no exceptions in the logs — a silent failure. Analyse the context and return ONLY valid JSON with keys: diagnosis (string), confidence (HIGH|MEDIUM|LOW), root_cause_hypothesis (string), proposed_fix (string), recommended_action (ROLLBACK|ESCALATE|INVESTIGATE), escalate (boolean)."
)

AGENT_CONFIG = {
    "model": "claude-opus-4-5-20251101",
    "max_tokens": 1024,
    "max_iterations": 3,
    "context_fields": [
        "trigger",
        "service",
        "deploy_id",
        "health_check",
        "logs"
    ]
}

def load_sample() -> str:
    sample = Path(__file__).parent / "sample_data.json"
    return sample.read_text()


def run_agent() -> dict:
    context = load_sample()

    if MOCK_MODE:
        print("[MOCK MODE] Skipping Claude API — returning pre-defined response.")
        print("[MOCK MODE] Note: MEDIUM confidence + escalate=true is the correct answer for silent 503s.\n")
        result = MOCK_RESPONSE
    else:
        # TODO: Call ask() with SYSTEM_PROMPT and the deployment context.
        #
        # ask() signature:
        #   ask(system=..., user=..., model=..., max_tokens=...)
        #
        # - system:     use SYSTEM_PROMPT (the silent 503 agent prompt above)
        # - user:       pass the context as  f"Context:\n{context}"
        # - model and max_tokens: use AGENT_CONFIG["model"] and AGENT_CONFIG["max_tokens"]
        #
        # Key teaching point: the correct answer here is MEDIUM confidence + escalate=true.
        # A silent 503 with no exceptions means you are inferring state, not reading a traceback.
        # Assign the return value to  result  so it flows into the print/save below.
        raise NotImplementedError(
            "Complete run_agent() — call ask() with SYSTEM_PROMPT and the context."
        )

    print(json.dumps(result, indent=2))
    save_json(result, module=4)
    print(to_step_summary(result, title="Module 4 Agent Result"))

    if result.get("escalate"):
        print("\n🔴 ESCALATION REQUIRED — creating GitHub Issue body:")
        print(to_github_issue(result, module=4))

    return result


if __name__ == "__main__":
    run_agent()
