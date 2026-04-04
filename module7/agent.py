"""
module7/agent.py
Entry point for Module 7 exercise: Orchestrator + specialist agents — route an incident to the right specialist

MOCK MODE
---------
Run without an API key to see the expected output format:
    python module7/agent.py --mock
    MOCK_MODE=1 python module7/agent.py

The mock response shows a HIGH conflict_risk routing decision — this triggers
the parallel investigation and conflict resolution path that is the core of Module 7.
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

MOCK_RESPONSE = {
    "primary_specialist": "incident_responder",
    "secondary_specialist": "cost_optimizer",
    "routing_reason": "Post-deploy error rate spike (+22%) requires immediate incident response. Cost optimizer is also relevant because the proposed rollback involves spinning up a previous version — a cost event that the FinOps agent should evaluate before the rollback is approved.",
    "parallel_investigation": True,
    "conflict_risk": "HIGH",
    "escalate": True,
    "confidence": "HIGH",
}

# ── Prompt & config ────────────────────────────────────────────────────────────
SYSTEM_PROMPT = (
    "You are an orchestrator agent that routes incidents to specialist agents. Analyse the incident and return ONLY valid JSON with keys: primary_specialist (string, one of available_specialists), secondary_specialist (string or null), routing_reason (string), parallel_investigation (boolean), conflict_risk (LOW|MEDIUM|HIGH), escalate (boolean), confidence (HIGH|MEDIUM|LOW)."
)

AGENT_CONFIG = {
    "model": "claude-opus-4-5-20251101",
    "max_tokens": 1024,
    "max_iterations": 1,
    "context_fields": [
        "incident",
        "available_specialists"
    ]
}

def load_sample() -> str:
    sample = Path(__file__).parent / "sample_data.json"
    return sample.read_text()


def run_agent() -> dict:
    context = load_sample()

    if MOCK_MODE:
        print("[MOCK MODE] Skipping Claude API — returning pre-defined response.")
        print("[MOCK MODE] HIGH conflict_risk triggers parallel investigation + escalation path.\n")
        result = MOCK_RESPONSE
    else:
        result = ask(
            system=SYSTEM_PROMPT,
            user=f"Context:\n{context}",
            model=AGENT_CONFIG["model"],
            max_tokens=AGENT_CONFIG["max_tokens"],
        )

    print(json.dumps(result, indent=2))
    save_json(result, module=7)
    print(to_step_summary(result, title="Module 7 Agent Result"))

    if result.get("escalate"):
        print("\n🔴 ESCALATION REQUIRED — creating GitHub Issue body:")
        print(to_github_issue(result, module=7))

    return result


if __name__ == "__main__":
    run_agent()
