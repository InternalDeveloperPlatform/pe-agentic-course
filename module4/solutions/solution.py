"""
module4/solutions/solution.py
Complete solution for Module 4 exercise: OOMKill Post-Deploy Triage

MOCK MODE: python module4/solutions/solution.py --mock
Key teaching point: MEDIUM confidence + escalate=true is CORRECT for state inference.
"""
import os, sys, json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from shared.claude_client import ask
from shared.output import save_json, to_step_summary, to_github_issue

MOCK_MODE = "--mock" in sys.argv or os.environ.get("MOCK_MODE") == "1"

MOCK_RESPONSE = {
    "diagnosis": "Service is returning 503 errors post-deploy with no application exceptions. Pattern suggests infrastructure-level failure rather than code defect.",
    "confidence": "MEDIUM",
    "root_cause_hypothesis": "A downstream dependency (database connection pool or external API) became unavailable after deployment triggered a configuration reload.",
    "proposed_fix": "Check downstream service health for payment-api and db-primary. Verify connection pool settings. If db-primary unreachable, restore previous connection string from secrets manager.",
    "recommended_action": "ESCALATE",
    "escalate": True,
}

SYSTEM_PROMPT = (
    "You are a deployment triage agent. The service is returning 503 errors post-deploy with no exceptions. "
    "Return ONLY valid JSON: diagnosis (string), confidence (HIGH|MEDIUM|LOW), "
    "root_cause_hypothesis (string), proposed_fix (string), "
    "recommended_action (ROLLBACK|ESCALATE|INVESTIGATE), escalate (boolean)."
)

def run():
    sample = (Path(__file__).parent.parent / "sample_data.json").read_text()

    if MOCK_MODE:
        print("[MOCK MODE] Note: MEDIUM + escalate=true is CORRECT for silent 503s.\n")
        result = MOCK_RESPONSE
    else:
        result = ask(system=SYSTEM_PROMPT, user=f"Context:\n{sample}", max_tokens=1024)

    print(json.dumps(result, indent=2))
    assert result["confidence"] == "MEDIUM", f"Expected MEDIUM, got {result['confidence']}"
    assert result["escalate"] is True, "Expected escalate=true for silent 503"
    print("\n✅ Confidence calibration verified: MEDIUM + escalate=True")

    save_json(result, module=4)
    print(to_step_summary(result, "Module 4 Agent Result"))
    if result.get("escalate"):
        print("\n🔴 ESCALATION REQUIRED"); print(to_github_issue(result, module=4))
    return result

if __name__ == "__main__":
    run()
