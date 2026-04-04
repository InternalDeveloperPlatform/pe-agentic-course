"""
module5/monitor.py
Post-Deploy Rollback Monitor — Module 5 companion script.

The quality gate agent (triage_agent.py) runs BEFORE deploy as a blocking
CI gate. This monitor runs AFTER deploy on a timed check, watching live
production signals to decide whether to recommend a rollback.

The two agents are intentionally separate:
- triage_agent.py → blocking gate → prevents bad deploys
- monitor.py      → post-deploy watch → catches what slipped through

Usage
-----
    python module5/monitor.py                   # real API call
    python module5/monitor.py --mock            # mock mode (no API key)
    python module5/monitor.py --deploy-id <id>  # specify deployment to monitor
    MOCK_MODE=1 python module5/monitor.py

How it works
------------
1. Reads the current deployment snapshot (sample_data.json or --deploy-id).
2. Evaluates live metrics against the rollback thresholds in quality-gates.json.
3. Calls Claude to synthesise a rollback recommendation with justification.
4. Outputs JSON with: rollback_recommended, severity, trigger, verification_steps.

Safety rules (enforced in SYSTEM_PROMPT):
- Never auto-rollback if db_migration_present=true (always escalate).
- Auto-rollback only fires if deploy_age_minutes < 30 AND previous_version is available.
- IMMEDIATE severity only if error_rate_pct > 10 AND p95_latency_ms > 2000.
"""

import os
import sys
import json
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from shared.claude_client import ask
from shared.output import save_json, to_step_summary, to_github_issue

# ── Mock mode ──────────────────────────────────────────────────────────────────
MOCK_MODE = "--mock" in sys.argv or os.environ.get("MOCK_MODE") == "1"

MOCK_RESPONSE = {
    "rollback_recommended": True,
    "severity":             "IMMEDIATE",
    "trigger":              "latency_p95_delta gate: P95 latency increased by 18.4% (threshold: 10%). Error rate at 2.1% — within tolerance but rising.",
    "rollback_target":      "v1.8.2",
    "rollback_rationale":   "P95 latency regression of 18.4% exceeds the rollback_trigger threshold of 10% within 8 minutes of deploy. Previous version v1.8.2 is available. Deploy age is 8 minutes, well within the 30-minute auto-rollback window. No database migration was present in this deploy, so rollback is safe.",
    "verification_steps":   [
        "Confirm P95 latency returns below 500ms within 2 minutes of rollback.",
        "Verify error rate drops below 0.5% within 5 minutes.",
        "Check checkout service health endpoint: curl -s https://api.example.com/checkout/health",
        "Confirm no orders were lost during the incident window (check orders table row count).",
    ],
    "escalate":             False,
}

# ── System prompt ──────────────────────────────────────────────────────────────
SYSTEM_PROMPT = """\
You are a post-deploy rollback monitor agent. You receive live production metrics
taken after a recent deployment and must decide whether to recommend a rollback.

Return ONLY valid JSON with these keys:
- rollback_recommended (boolean): true if you recommend rolling back
- severity (IMMEDIATE|SCHEDULED|OPTIONAL|NONE): urgency of the rollback
- trigger (string): which gate or metric triggered the recommendation
- rollback_target (string): version or commit SHA to roll back to
- rollback_rationale (string): one-paragraph justification including evidence
- verification_steps (list of strings): steps to confirm recovery after rollback
- escalate (boolean): true if this requires human decision before any action

Safety rules you MUST follow:
1. If db_migration_present is true, ALWAYS set escalate=true. Never recommend IMMEDIATE rollback when a migration is involved.
2. Only recommend rollback if deploy_age_minutes < 30 AND rollback_available=true.
3. IMMEDIATE severity requires BOTH error_rate_pct > 10 AND p95_latency_ms > 2000.
4. If no rollback_trigger gate has failed, set rollback_recommended=false and severity=NONE.
5. The agent recommends — a human approves. Never suggest autonomous execution.
"""

AGENT_CONFIG = {
    "model":      "claude-opus-4-5-20251101",
    "max_tokens": 1024,
}


def load_deployment(deploy_id: str | None) -> dict:
    """Load the deployment snapshot to monitor."""
    sample = Path(__file__).parent / "sample_data.json"
    data = json.loads(sample.read_text())
    if deploy_id:
        data["deploy_id"] = deploy_id
    return data


def load_gates() -> list:
    """Load rollback-trigger gates from quality-gates.json."""
    gates_path = Path(__file__).parent / "quality-gates.json"
    if not gates_path.exists():
        return []
    gates_data = json.loads(gates_path.read_text())
    return [g for g in gates_data.get("gates", []) if g.get("rollback_trigger")]


def run_monitor(deployment: dict, gates: list) -> dict:
    """Evaluate deployment health and return rollback recommendation."""
    if MOCK_MODE:
        print("[MOCK MODE] Skipping Claude API — returning pre-defined rollback assessment.")
        print("[MOCK MODE] Set ANTHROPIC_API_KEY and remove --mock to call the real API.\n")
        return MOCK_RESPONSE

    context = {
        "deployment": deployment,
        "rollback_trigger_gates": gates,
    }

    return ask(
        system=SYSTEM_PROMPT,
        user=f"Post-deploy monitoring snapshot:\n\n{json.dumps(context, indent=2)}",
        model=AGENT_CONFIG["model"],
        max_tokens=AGENT_CONFIG["max_tokens"],
    )


def main():
    parser = argparse.ArgumentParser(description="Module 5 Post-Deploy Rollback Monitor")
    parser.add_argument("--deploy-id", help="Deployment ID to monitor")
    parser.add_argument("--mock",      action="store_true", help="Run in mock mode")
    args = parser.parse_args()

    deployment = load_deployment(args.deploy_id)
    gates      = load_gates()

    deploy_id = deployment.get("deploy_id", "unknown")
    service   = deployment.get("service",   "unknown")
    print(f"[monitor] Checking deployment {deploy_id} for service '{service}'")
    print(f"[monitor] Loaded {len(gates)} rollback-trigger gate(s) from quality-gates.json\n")

    result = run_monitor(deployment, gates)

    print(json.dumps(result, indent=2))
    save_json(result, module=5, label="monitor")
    print(to_step_summary(result, title="Module 5 Rollback Monitor Result"))

    if result.get("rollback_recommended"):
        severity = result.get("severity", "UNKNOWN")
        print(f"\n🔴 ROLLBACK RECOMMENDED — severity: {severity}")
        if result.get("escalate"):
            print("   ⚠️  Human approval required before rollback (escalate=true)")
            print(to_github_issue(result, module=5))
        else:
            print("   Agent recommendation is self-contained. Awaiting human approval to execute.")
    else:
        print("\n✅ No rollback recommended — deployment appears healthy")

    return result


if __name__ == "__main__":
    main()
