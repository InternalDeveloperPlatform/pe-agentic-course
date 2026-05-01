"""
module7/solutions/solution.py
Reference solution for Module 7: Multi-Agent Orchestrator.

What this module teaches
------------------------
The Orchestrator Mediation pattern: two specialist agents run in parallel threads,
their outputs are compared for conflicts, and the orchestrator decides what to do
based on the conflict type.

    Event → Orchestrator → [Gate Agent ‖ Rollback Agent] → Conflict Check → Output

Key design rules:
  1. Specialists never communicate with each other directly.
     All information flows through the orchestrator.
  2. Safety First: when agents contradict each other on a live system, escalate —
     do not try to find a compromise. Deployment approval is reversible;
     a live incident is not.
  3. The conflict detector implements ONE rule: if the gate says APPROVE and the
     rollback agent says IMMEDIATE, the rollback agent wins. Always.

What you implemented in the exercise (orchestrator.py)
------------------------------------------------------
Three functions:

    def run_gate_agent(context: dict) -> dict:
        # Call ask() with GATE_SYSTEM_PROMPT
        # The context dict contains pipeline results and gate thresholds

    def run_rollback_agent(context: dict) -> dict:
        # Call ask() with ROLLBACK_SYSTEM_PROMPT
        # The context dict contains post-deploy metrics and deploy metadata

    def detect_conflict(gate_result: dict, rollback_result: dict) -> dict:
        # Compare the two outputs:
        #   APPROVE + IMMEDIATE  → HARD_CONFLICT  → SAFETY_FIRST_ESCALATE
        #   APPROVE* + SCHEDULED → SOFT_CONFLICT  → SOFT_ESCALATE
        #   consistent           → no conflict    → SYNTHESISE

These three functions are shown below with inline comments explaining
each design decision.

Compare with: module7/orchestrator.py (the full exercise file)

Run
---
    python module7/solutions/solution.py --mock
    python module7/solutions/solution.py --mock --scenario no_conflict
    python module7/solutions/solution.py --mock --scenario partial_conflict
    python module7/solutions/solution.py --mock --scenario full_conflict
    ANTHROPIC_API_KEY=sk-... python module7/solutions/solution.py --scenario full_conflict
"""

import os
import sys
import json
import argparse
import concurrent.futures
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from shared.claude_client import ask
from shared.output import save_json, to_step_summary, to_github_issue

# ── Mock mode ──────────────────────────────────────────────────────────────────
MOCK_MODE = "--mock" in sys.argv or os.environ.get("MOCK_MODE") == "1"

# ── Mock scenarios — one per conflict type ─────────────────────────────────────
# Each scenario provides pre-baked responses for both agents and the expected
# conflict detection output. In mock mode these are returned directly so you
# can verify the orchestration logic without calling the API.
MOCK_SCENARIOS = {
    "no_conflict": {
        "gate_result": {
            "decision":        "APPROVE",
            "confidence":      "HIGH",
            "rationale":       "All 6 quality gates pass. Test coverage 96.2%, zero SAST findings, Lighthouse 91/100.",
            "blocking_issues": [],
            "conditions":      [],
            "risk_score":      "LOW",
            "escalate":        False,
        },
        "rollback_result": {
            "rollback_recommended": False,
            "severity":             "NONE",
            "trigger":              "No rollback-trigger gates failed.",
            "rollback_target":      None,
            "escalate":             False,
        },
        "conflict": {
            "detected":   False,
            "type":       None,
            "resolution": "SYNTHESISE",
            "summary":    "Gate Agent: APPROVE. Rollback Agent: no rollback. Consistent — safe to deploy.",
        },
    },
    "partial_conflict": {
        "gate_result": {
            "decision":        "APPROVE_WITH_CONDITIONS",
            "confidence":      "MEDIUM",
            "rationale":       "Coverage at 74% (below 80% threshold) but not regressed. No critical failures.",
            "blocking_issues": [],
            "conditions":      ["Coverage must not regress below 74% in next 3 PRs"],
            "risk_score":      "MEDIUM",
            "escalate":        False,
        },
        "rollback_result": {
            "rollback_recommended": True,
            "severity":             "SCHEDULED",
            "trigger":              "latency_p95_delta: P95 latency increased 7.2% — below the 10% immediate rollback trigger.",
            "rollback_target":      "v1.8.2",
            "escalate":             False,
        },
        "conflict": {
            "detected":   True,
            "type":       "SOFT_CONFLICT",
            "resolution": "SOFT_ESCALATE",
            "summary":    (
                "Gate Agent: APPROVE_WITH_CONDITIONS. Rollback Agent: SCHEDULED rollback. "
                "Soft conflict — inform on-call but no immediate action required."
            ),
        },
    },
    "full_conflict": {
        "gate_result": {
            "decision":        "APPROVE",
            "confidence":      "HIGH",
            "rationale":       "CI pipeline passed all gates before deploy. Snapshot taken 45 minutes ago.",
            "blocking_issues": [],
            "conditions":      [],
            "risk_score":      "LOW",
            "escalate":        False,
        },
        "rollback_result": {
            "rollback_recommended": True,
            "severity":             "IMMEDIATE",
            "trigger":              "latency_p95_delta exceeded 18.4% and error_rate_pct > 10% post-deploy.",
            "rollback_target":      "v1.8.2",
            "escalate":             False,
        },
        "conflict": {
            "detected":   True,
            "type":       "HARD_CONFLICT",
            "resolution": "SAFETY_FIRST_ESCALATE",
            "summary":    (
                "Gate Agent: APPROVE (stale pre-deploy snapshot). "
                "Rollback Agent: IMMEDIATE rollback (live post-deploy data). "
                "Hard conflict — Safety First: escalate and halt all deploys until human reviews."
            ),
        },
    },
}

# ── System prompts ─────────────────────────────────────────────────────────────
# Each specialist receives a focused system prompt that defines its role and
# output schema. The prompts are independent — neither specialist knows the other exists.

GATE_SYSTEM_PROMPT = """\
You are a quality gate evaluation agent. Assess the deployment pipeline data and
return ONLY valid JSON with keys:
- decision (APPROVE|APPROVE_WITH_CONDITIONS|HOLD): overall gate decision
- confidence (HIGH|MEDIUM|LOW): confidence in the assessment
- rationale (string): one-paragraph explanation
- blocking_issues (list of strings): empty if APPROVE
- conditions (list of strings): empty if APPROVE
- risk_score (LOW|MEDIUM|HIGH): deployment risk level
- escalate (boolean): true if human must review before proceeding
"""

ROLLBACK_SYSTEM_PROMPT = """\
You are a post-deploy rollback monitor agent. Evaluate the live metrics and
return ONLY valid JSON with keys:
- rollback_recommended (boolean): true if rollback is recommended
- severity (IMMEDIATE|SCHEDULED|OPTIONAL|NONE): urgency of the recommendation
- trigger (string): which metric or threshold triggered the recommendation
- rollback_target (string|null): version or SHA to roll back to
- escalate (boolean): true if human must approve before rollback

Safety rules:
- Never recommend IMMEDIATE rollback if db_migration_present=true.
- Only recommend rollback if deploy_age_minutes < 30 AND rollback_available=true.
"""

AGENT_CONFIG = {
    "model":      "claude-opus-4-5-20251101",
    "max_tokens": 1024,
}


def load_sample() -> dict:
    """Load the platform incident event from sample_data.json."""
    return json.loads((Path(__file__).parent.parent / "sample_data.json").read_text())


# ── Specialist agent functions ─────────────────────────────────────────────────

def run_gate_agent(context: dict) -> dict:
    """
    Gate Agent — evaluates the pre-deploy quality gates.

    Implementation notes:
    - The context contains pipeline results, coverage metrics, and SAST findings.
    - GATE_SYSTEM_PROMPT constrains Claude to the 7-key output schema.
    - This function is designed to run in a thread (via ThreadPoolExecutor).
      It has no shared state and is safe to call concurrently.
    - The gate evaluates data from BEFORE the deploy (CI results, static analysis).
      It cannot see live production metrics — that's the rollback agent's job.
    """
    if MOCK_MODE:
        print("[gate_agent] [MOCK] Returning pre-defined gate evaluation.")
        return {}   # main() fills this from MOCK_SCENARIOS[scenario]

    return ask(
        system=GATE_SYSTEM_PROMPT,
        user=f"Pipeline data:\n{json.dumps(context, indent=2)}",
        model=AGENT_CONFIG["model"],
        max_tokens=AGENT_CONFIG["max_tokens"],
    )


def run_rollback_agent(context: dict) -> dict:
    """
    Rollback Agent — evaluates post-deploy production signals.

    Implementation notes:
    - The context contains live metrics: error rates, latency deltas, memory usage.
    - ROLLBACK_SYSTEM_PROMPT includes safety rules (no rollback during migrations)
      that give Claude explicit guardrails beyond its default reasoning.
    - This function is also thread-safe and runs concurrently with run_gate_agent().
    - The rollback agent sees data from AFTER the deploy (live signals, not CI results).
      This is why it can conflict with the gate agent: the gate approved based on
      pre-deploy data; the rollback agent is seeing post-deploy reality.
    """
    if MOCK_MODE:
        print("[rollback_agent] [MOCK] Returning pre-defined rollback assessment.")
        return {}   # main() fills this from MOCK_SCENARIOS[scenario]

    return ask(
        system=ROLLBACK_SYSTEM_PROMPT,
        user=f"Post-deploy metrics:\n{json.dumps(context, indent=2)}",
        model=AGENT_CONFIG["model"],
        max_tokens=AGENT_CONFIG["max_tokens"],
    )


def detect_conflict(gate_result: dict, rollback_result: dict) -> dict:
    """
    Conflict detector — compares the two agent outputs and classifies the result.

    This is the orchestrator's core logic. It implements three rules:

    HARD_CONFLICT (SAFETY_FIRST_ESCALATE)
        Gate says APPROVE but Rollback says IMMEDIATE rollback.
        These agents are looking at different data (pre-deploy vs live).
        When they contradict each other on a live system, Safety First applies:
        escalate immediately, halt all deploys, wait for a human.

    SOFT_CONFLICT (SOFT_ESCALATE)
        Gate says APPROVE or APPROVE_WITH_CONDITIONS, Rollback says SCHEDULED.
        The system is not in immediate danger but drifting toward a problem.
        Inform on-call but no automatic action required yet.

    No conflict (SYNTHESISE)
        Agents agree. Gate says deploy is safe and Rollback sees no reason
        to roll back. Produce a unified recommendation.

    Implementation note:
        gate_decision.startswith("APPROVE") catches both "APPROVE" and
        "APPROVE_WITH_CONDITIONS" without needing to list both explicitly.
    """
    gate_decision     = gate_result.get("decision", "")
    rollback_severity = rollback_result.get("severity", "NONE")

    if gate_decision == "APPROVE" and rollback_severity == "IMMEDIATE":
        # SAFETY FIRST: the gate approved based on stale pre-deploy data.
        # The rollback agent has live post-deploy evidence of a problem.
        # The rollback agent wins — always.
        return {
            "detected":   True,
            "type":       "HARD_CONFLICT",
            "resolution": "SAFETY_FIRST_ESCALATE",
            "summary": (
                f"Gate Agent: {gate_decision} (stale pre-deploy snapshot). "
                "Rollback Agent: IMMEDIATE rollback (live post-deploy data). "
                "Hard conflict — Safety First: escalate and halt all deploys until human reviews."
            ),
        }

    elif gate_decision.startswith("APPROVE") and rollback_severity == "SCHEDULED":
        # Soft conflict: system is degrading but not in immediate danger.
        # Inform on-call; no automated action yet.
        return {
            "detected":   True,
            "type":       "SOFT_CONFLICT",
            "resolution": "SOFT_ESCALATE",
            "summary": (
                f"Gate Agent: {gate_decision}. Rollback Agent: SCHEDULED rollback. "
                "Soft conflict — inform on-call but no immediate action required."
            ),
        }

    else:
        # Agents are consistent. Gate approved and rollback sees no issues.
        return {
            "detected":   False,
            "type":       None,
            "resolution": "SYNTHESISE",
            "summary": (
                f"Gate Agent: {gate_decision}. Rollback Agent: {rollback_severity}. "
                "Consistent — safe to proceed with deployment."
            ),
        }


# ── Main ───────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Module 7 Multi-Agent Orchestrator — Solution")
    parser.add_argument(
        "--scenario",
        choices=list(MOCK_SCENARIOS.keys()),
        default="full_conflict",
        help="Conflict scenario for mock mode (default: full_conflict)",
    )
    parser.add_argument("--mock", action="store_true", help="Run in mock mode — no API key needed")
    args = parser.parse_args()

    context = load_sample()
    print(f"[orchestrator] Loaded incident: {context.get('incident', {}).get('id', 'unknown')}")

    if MOCK_MODE:
        # In mock mode, use pre-baked responses for the selected scenario.
        # The agent functions return {} in mock mode; main() fills them in here.
        scenario_data   = MOCK_SCENARIOS[args.scenario]
        gate_result     = scenario_data["gate_result"]
        rollback_result = scenario_data["rollback_result"]
        conflict        = scenario_data["conflict"]
        print(f"[orchestrator] [MOCK MODE] Scenario: {args.scenario}\n")
        print("[gate_agent] [MOCK] Returning pre-defined gate evaluation.")
        print("[rollback_agent] [MOCK] Returning pre-defined rollback assessment.")
    else:
        # Real mode: run both agents in parallel using ThreadPoolExecutor.
        # Both functions are I/O-bound (waiting for the Claude API response),
        # so threading gives a real speedup: both API calls happen concurrently
        # rather than sequentially. Wall-clock time ≈ max(gate_latency, rollback_latency)
        # instead of gate_latency + rollback_latency.
        print("[orchestrator] Running Gate Agent and Rollback Agent in parallel...")
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
            gate_future     = executor.submit(run_gate_agent,     context)
            rollback_future = executor.submit(run_rollback_agent, context)
            # .result() blocks until each future completes (no timeout here;
            # Claude API calls typically complete in 2–5 seconds)
            gate_result     = gate_future.result()
            rollback_result = rollback_future.result()

        conflict = detect_conflict(gate_result, rollback_result)

    # ── Output ──────────────────────────────────────────────────────────────────
    result = {
        "gate_agent":     gate_result,
        "rollback_agent": rollback_result,
        "conflict":       conflict,
    }

    print("\n── Gate Agent ────────────────────────────────────────────────")
    print(json.dumps(gate_result, indent=2))
    print("\n── Rollback Agent ────────────────────────────────────────────")
    print(json.dumps(rollback_result, indent=2))
    print("\n── Conflict Analysis ─────────────────────────────────────────")
    print(json.dumps(conflict, indent=2))

    save_json(result, module=7, label="orchestrator")
    print(to_step_summary(result, title="Module 7 Solution Result"))

    resolution = conflict.get("resolution", "")
    if "ESCALATE" in resolution:
        print(f"\n🔴 ESCALATION REQUIRED — resolution: {resolution}")
        print(to_github_issue(result, module=7))
    else:
        print("\n✅ No conflict — safe to deploy")

    return result


if __name__ == "__main__":
    main()
