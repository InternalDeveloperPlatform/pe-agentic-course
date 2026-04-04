"""
module2/solutions/solution.py
Complete solution for Module 2 exercise: Five-Step Agentic Loop

MOCK MODE: python module2/solutions/solution.py --mock
"""
import os, sys, json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from shared.claude_client import ask
from shared.output import save_json, to_step_summary, to_github_issue

MOCK_MODE = "--mock" in sys.argv or os.environ.get("MOCK_MODE") == "1"

MOCK_RESPONSE = {
    "diagnosis": "The deployment failed due to a missing environment variable PAYMENT_API_KEY in the production environment.",
    "confidence": "HIGH",
    "recommended_action": "Add PAYMENT_API_KEY to GitHub Actions secrets and reference it in the workflow env block.",
    "escalate": False,
}

SYSTEM_PROMPT = (
    "You are a CI/CD diagnostic agent. Analyse the build log and return ONLY valid JSON "
    "with keys: diagnosis (string), confidence (HIGH|MEDIUM|LOW), "
    "recommended_action (string), escalate (boolean)."
)

def step1_write_prompt(log: str) -> tuple:
    """Step 1: Write the system prompt and user message."""
    user_msg = f"Build log:\n{log}\n\nDiagnose the failure. Identify root cause, confidence, and recommended action."
    return SYSTEM_PROMPT, user_msg

def step2_call_api(system: str, user: str) -> dict:
    """Step 2: Call the Claude API (or return mock)."""
    if MOCK_MODE:
        print("[MOCK MODE] Skipping Claude API.\n")
        return MOCK_RESPONSE
    return ask(system=system, user=user, max_tokens=1024)

def step3_parse_json(result: dict) -> dict:
    """Step 3: Parse and validate the JSON response."""
    required = {"diagnosis", "confidence", "recommended_action", "escalate"}
    missing = required - set(result.keys())
    if missing:
        raise ValueError(f"Agent response missing required fields: {missing}")
    return result

def step4_execute_action(result: dict):
    """Step 4: Execute the recommended action."""
    print(f"\n[ACTION] Confidence: {result['confidence']}")
    print(f"[ACTION] Recommended: {result['recommended_action']}")
    if result["escalate"]:
        print("[ACTION] 🔴 ESCALATION REQUIRED")
        print(to_github_issue(result, module=2))
    else:
        print("[ACTION] ✅ No escalation needed — agent handled autonomously")

def step5_verify_result(result: dict) -> bool:
    """Step 5: Verify the result meets success criteria."""
    return result["confidence"] in ("HIGH", "MEDIUM", "LOW") and bool(result["recommended_action"])

def run():
    log = (Path(__file__).parent.parent / "sample_log.txt").read_text()
    system, user = step1_write_prompt(log)
    raw_result = step2_call_api(system, user)
    result = step3_parse_json(raw_result)
    step4_execute_action(result)
    success = step5_verify_result(result)
    save_json(result, module=2)
    print(to_step_summary(result, "Module 2 Agent Result"))
    print(f"\n[VERIFY] All checks passed: {success}")
    return result

if __name__ == "__main__":
    run()
