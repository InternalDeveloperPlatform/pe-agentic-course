"""
module5/solutions/solution.py
Complete solution for Module 5 exercise: Quality Gate with Six Threshold Dimensions

MOCK MODE: python module5/solutions/solution.py --mock
"""
import os, sys, json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from shared.claude_client import ask
from shared.output import save_json, to_step_summary, to_github_issue

MOCK_MODE = "--mock" in sys.argv or os.environ.get("MOCK_MODE") == "1"

MOCK_RESPONSE = {
    "decision": "APPROVE_WITH_CONDITIONS",
    "confidence": "HIGH",
    "rationale": "All critical gates pass: test pass rate 97.3%, zero SAST HIGH findings, Lighthouse 91/100. Coverage 74.1% is below the 80% threshold but has not regressed. Friday deploy window elevates risk.",
    "blocking_issues": [],
    "conditions": [
        "Coverage must not regress below 74% in the next three PRs",
        "Deploy should target off-peak hours (before 14:00 UTC)",
        "Monitor error rate for 15 minutes post-deploy"
    ],
    "risk_score": "MEDIUM",
    "recommended_deploy_window": "Before 14:00 UTC today or defer to Monday 09:00 UTC",
    "change_risk_score": "HIGH",
    "change_risk_reason": "Friday deploy with 623 lines changed across 14 files — exceeds 500-line threshold",
    "escalate": False,
}

SYSTEM_PROMPT = (
    "You are a release readiness evaluation agent with six gate dimensions: "
    "Correctness (test_pass_rate >= 95%), Coverage (line_coverage >= 80%), "
    "Security (no SAST HIGH findings), Performance (lighthouse >= 85), "
    "Cost (cost_delta <= 10%), Change Risk (HIGH if Friday + >500 lines changed). "
    "Return ONLY valid JSON: decision (APPROVE|APPROVE_WITH_CONDITIONS|HOLD), "
    "confidence (HIGH|MEDIUM|LOW), rationale (string), blocking_issues (list), "
    "conditions (list), risk_score (LOW|MEDIUM|HIGH), recommended_deploy_window (string), "
    "change_risk_score (LOW|MEDIUM|HIGH), change_risk_reason (string), escalate (boolean)."
)

def run():
    sample = (Path(__file__).parent.parent / "sample_data.json").read_text()

    if MOCK_MODE:
        print("[MOCK MODE] Shows APPROVE_WITH_CONDITIONS — typical borderline gate result.\n")
        result = MOCK_RESPONSE
    else:
        result = ask(system=SYSTEM_PROMPT, user=f"Pipeline results:\n{sample}", max_tokens=1024)

    print(json.dumps(result, indent=2))
    save_json(result, module=5)
    print(to_step_summary(result, "Module 5 Agent Result"))
    if result.get("escalate"):
        print("\n🔴 ESCALATION REQUIRED"); print(to_github_issue(result, module=5))
    return result

if __name__ == "__main__":
    run()
