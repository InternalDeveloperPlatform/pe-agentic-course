"""
module6/agent.py
Entry point for Module 6 exercise: Conversational ops agent — answer natural-language questions about platform health

MOCK MODE
---------
Run without an API key to see the expected output format:
    python module6/agent.py --mock
    MOCK_MODE=1 python module6/agent.py

The mock response demonstrates the conversational interface pattern:
plain-English answer + causal chain + follow-up questions.
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
    "answer": "The checkout-service is experiencing elevated latency (p95 = 2.3s, up from 0.4s baseline). This started at 14:32 UTC, 8 minutes after the last deployment. The payment-api dependency is showing a 40% error rate which is the most likely causal factor.",
    "causal_chain": [
        "checkout-service deployment completed at 14:24 UTC",
        "payment-api error rate began rising at 14:32 UTC (8-minute lag)",
        "checkout-service latency spiked as retries accumulated against failing payment-api",
        "downstream: cart-service timeout rate increased as checkout responses slowed"
    ],
    "confidence": "MEDIUM",
    "follow_up_questions": [
        "Was there a simultaneous change to payment-api at or before 14:32 UTC?",
        "What does the payment-api error response body contain — rate limit, timeout, or 5xx?"
    ],
    "escalate": True,
}

# ── Prompt & config ────────────────────────────────────────────────────────────
SYSTEM_PROMPT = (
    "You are a conversational platform observability agent. You receive live metrics, recent alerts, and a natural-language question from an engineer. Return ONLY valid JSON with keys: answer (string, plain English, max 3 sentences), causal_chain (list of strings, each a step in the causal path), confidence (HIGH|MEDIUM|LOW), follow_up_questions (list of 2 strings), escalate (boolean)."
)

AGENT_CONFIG = {
    "model": "claude-opus-4-5-20251101",
    "max_tokens": 1024,
    "max_iterations": 1,
    "context_fields": [
        "metrics",
        "recent_alerts",
        "user_question"
    ]
}

def load_sample() -> str:
    sample = Path(__file__).parent / "sample_data.json"
    return sample.read_text()


def run_agent() -> dict:
    context = load_sample()

    if MOCK_MODE:
        print("[MOCK MODE] Skipping Claude API — returning pre-defined response.")
        print("[MOCK MODE] Shows conversational answer + causal chain + follow-up questions.\n")
        result = MOCK_RESPONSE
    else:
        result = ask(
            system=SYSTEM_PROMPT,
            user=f"Context:\n{context}",
            model=AGENT_CONFIG["model"],
            max_tokens=AGENT_CONFIG["max_tokens"],
        )

    print(json.dumps(result, indent=2))
    save_json(result, module=6)
    print(to_step_summary(result, title="Module 6 Agent Result"))

    if result.get("escalate"):
        print("\n🔴 ESCALATION REQUIRED — creating GitHub Issue body:")
        print(to_github_issue(result, module=6))

    return result


if __name__ == "__main__":
    run_agent()
