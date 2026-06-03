"""
module2/agent.py
Entry point for Module 2 exercise: Five-step agentic loop — diagnose a
deployment failure

MOCK MODE
---------
Run without an API key to see the expected output format:
    python module2/agent.py --mock
    MOCK_MODE=1 python module2/agent.py
"""

import os
import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from shared.claude_client import ask
from shared.output import save_json, to_step_summary, to_github_issue

# ── Mock mode flag ───────────────────────────────────────────────────────────
MOCK_MODE = "--mock" in sys.argv or os.environ.get("MOCK_MODE") == "1"

MOCK_RESPONSE = {
    "diagnosis":
        "The deployment failed due to a missing environment variable "
        "PAYMENT_API_KEY in the production environment. The application "
        "starts successfully but crashes at the first payment request.",
    "confidence":
        "HIGH",
    "recommended_action":
        "Add PAYMENT_API_KEY to GitHub Actions secrets and reference it in "
        "the workflow env block. Re-trigger the deployment after confirming "
        "the secret is present.",
    "escalate":
        False,
}

# ── Prompt & config ──────────────────────────────────────────────────────────
# TODO: Write the system prompt for the triage agent.
#
# Your prompt should tell Claude:
# 1. Its role (e.g. "You are a CI/CD diagnostic agent")
# 2. To return ONLY valid JSON (no prose, no markdown)
# 3. The required JSON keys:
#      - diagnosis (string): root cause of the failure
#      - confidence (HIGH|MEDIUM|LOW): HIGH only when the root cause is
#        confirmed in logs
#      - recommended_action (string): concrete next step
#      - escalate (boolean): true if a human must review before taking action
#
# Hint: look at MOCK_RESPONSE above for the expected output shape.
SYSTEM_PROMPT = """
You are a CI/CD diagnostic agent specialized in analyzing pipeline failures,
build errors, and deployment issues.

Your job is to examine logs, error messages, and contextual information to
identify the root cause of failures and recommend actionable next steps.

You MUST respond with ONLY valid JSON — no prose, no markdown, no code fences,
no explanation before or after.

Required JSON structure:
{
  "diagnosis":
    "<string: the root cause of the failure>",
  "confidence":
    "<HIGH | MEDIUM | LOW>",
  "recommended_action":
    "<string: a concrete, specific next step to resolve the issue>",
  "escalate":
    <true | false>
}

Field rules:
- diagnosis: Be specific. Name the failing step, service, or component and what
  went wrong (e.g. "Unit test 'test_auth.py::test_login' failed due to a 
  missing environment variable: DATABASE_URL").
- confidence: Set to HIGH only when the root cause is explicitly confirmed in 
  the provided logs or output. Use MEDIUM when the cause is strongly implied 
  but not directly shown. Use LOW when you are inferring from 
  limited information.
- recommended_action: Provide a concrete next step a developer can act on 
  immediately (e.g. "Add DATABASE_URL to the CI environment secrets in the 
  repository settings").
- escalate: Set to true if the failure involves a production deployment, 
  security concern, data loss risk, or any situation where a human must 
  review before taking action.

Do not include any text outside the JSON object.
"""

AGENT_CONFIG = {
    "model": "claude-opus-4-5-20251101",
    "max_tokens": 1024,
    "max_iterations": 3,
    "context_fields": [
        "log_snippet",
        "build_number",
        "repo"
    ]
}


def load_sample() -> str:
    sample = Path(__file__).parent / "sample_log.txt"
    return sample.read_text()


def run_agent() -> dict:
    context = load_sample()

    if MOCK_MODE:
        print("[MOCK MODE] Skipping Claude API — returning pre-defined "
              "response.")
        print("[MOCK MODE] Set ANTHROPIC_API_KEY and remove --mock to "
              "call the real API.\n")
        result = MOCK_RESPONSE
    else:
        # TODO: Call ask() with SYSTEM_PROMPT and the log content.
        #
        # ask() signature:
        #   ask(system=..., user=..., model=..., max_tokens=...)
        #
        result = ask(
            system=SYSTEM_PROMPT, 
            user=f"Context:\n{context}\n\nDiagnose the failure. Identify root cause, confidence level, and recommended action.",
            model=AGENT_CONFIG["model"],
            max_tokens=AGENT_CONFIG["max_tokens"]
        )
        # - system: use SYSTEM_PROMPT (defined above)
        # - user:   pass the log as  f"Context:\n{context}"
        # - model and max_tokens: use AGENT_CONFIG["model"]
        #   and AGENT_CONFIG["max_tokens"]
        #
        # Assign the return value to `result`.
       
    print(json.dumps(result, indent=2))
    save_json(result, module=2)
    print(to_step_summary(result, title="Module 2 Agent Result"))

    if result.get("escalate"):
        print("\n🔴 ESCALATION REQUIRED — creating GitHub Issue body:")
        print(to_github_issue(result, module=2))

    return result


if __name__ == "__main__":
    run_agent()
