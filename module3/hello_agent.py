"""
module3/hello_agent.py
ReAct Agent — Module 3 exercise script.

This script extends module2/triage_agent.py into our first ReAct (Reason + Act)
agent. The agent iterates — Thought → Action → Observation — until it either
reaches a conclusion (finished=True) or exhausts max_iterations.

Usage
-----
    python module3/hello_agent.py                               # default scenario
    python module3/hello_agent.py --scenario "Kubernetes pod stuck in Pending"
    python module3/hello_agent.py --mock                        # no API key
    MOCK_MODE=1 python module3/hello_agent.py                   # same via env var

The --scenario flag lets you test the agent against any incident description
without editing the file — useful for live demos.

What's new vs module2/triage_agent.py
--------------------------------------
- ReAct loop: agent iterates up to max_iterations times
- Each iteration: { thought, action, observation, finished, confidence, recommended_action, escalate }
- Loop terminates when finished=True or max_iterations is reached
- History of all previous iterations is passed back each round (growing context)

Reference implementation: module3/solutions/solution.py
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
    "thought":            "The pod shows exit code 137 which is SIGKILL from the OOM killer. Restart count of 8 in 20 minutes confirms repeated OOM kills, not application crashes.",
    "action":             "Check memory requests/limits in the pod spec against actual peak usage from the metrics snapshot.",
    "observation":        "Pod requests 512Mi but peak usage before kill was 1.2Gi. The 512Mi limit is too low for peak load. No application code change triggered this.",
    "finished":           True,
    "confidence":         "HIGH",
    "recommended_action": "kubectl patch deployment checkout-api to set memory limit to 2Gi, then monitor for 10 minutes.",
    "escalate":           False,
}

# ── System prompt ──────────────────────────────────────────────────────────────
SYSTEM_PROMPT = """\
You are a ReAct-pattern incident analysis agent. On each iteration, reason about
the incident, propose one investigation action, simulate the observation, and decide
if you have enough information to conclude.

Return ONLY valid JSON with these keys:
- thought (string): your reasoning about the current state of the incident
- action (string): one specific investigation step to take next
- observation (string): what you would find if you executed that action
- finished (boolean): true only when you have a definitive conclusion
- confidence (HIGH|MEDIUM|LOW): confidence in your current assessment
- recommended_action (string): concrete remediation — include only when finished=true
- escalate (boolean): true if human intervention is required before a fix can be applied

Rules:
- Take exactly one action per iteration. Do not jump to conclusions in iteration 1.
- HIGH confidence is only appropriate for deterministic errors (NameError, OOMKill with clear metrics).
- MEDIUM confidence is correct when you are inferring state (silent failures, flapping services).
- If finished=false, leave recommended_action as an empty string.
"""

AGENT_CONFIG = {
    "model":          "claude-opus-4-5-20251101",
    "max_tokens":     1024,
    "max_iterations": 5,
}


def load_scenario(scenario_override: str | None) -> str:
    """Return the incident scenario text."""
    if scenario_override:
        return scenario_override
    sample = Path(__file__).parent / "sample_data.json"
    data = json.loads(sample.read_text())
    # Flatten the sample data into a readable incident description
    return json.dumps(data, indent=2)


def run_agent(scenario: str) -> dict:
    """Run the ReAct loop until finished=True or max_iterations reached."""
    if MOCK_MODE:
        print("[MOCK MODE] Skipping Claude API — returning single pre-defined iteration.")
        print("[MOCK MODE] In real mode this runs up to 5 ReAct iterations.\n")
        return MOCK_RESPONSE

    history = []
    result = {}

    for i in range(AGENT_CONFIG["max_iterations"]):
        if history:
            user_msg = (
                f"Incident context:\n{scenario}\n\n"
                f"Previous iterations:\n{json.dumps(history, indent=2)}"
            )
        else:
            user_msg = f"Incident context:\n{scenario}"

        result = ask(
            system=SYSTEM_PROMPT,
            user=user_msg,
            model=AGENT_CONFIG["model"],
            max_tokens=AGENT_CONFIG["max_tokens"],
        )

        print(f"\n── Iteration {i + 1} ──────────────────────────────────────────")
        print(json.dumps(result, indent=2))

        history.append(result)

        if result.get("finished"):
            print(f"\n[hello_agent] Concluded after {i + 1} iteration(s).")
            break
    else:
        print(f"\n[hello_agent] Reached max_iterations ({AGENT_CONFIG['max_iterations']}) without finishing.")

    return result


def main():
    parser = argparse.ArgumentParser(description="Module 3 ReAct Agent")
    parser.add_argument("--scenario", help="Incident description (overrides sample_data.json)")
    parser.add_argument("--mock",     action="store_true", help="Run in mock mode (no API call)")
    args = parser.parse_args()

    scenario = load_scenario(args.scenario)

    print(f"[hello_agent] Running ReAct agent on scenario:")
    print(f"  {scenario[:120].strip()}{'...' if len(scenario) > 120 else ''}\n")

    result = run_agent(scenario)

    print("\n── Final result ──────────────────────────────────────────────")
    print(json.dumps(result, indent=2))
    save_json(result, module=3)
    print(to_step_summary(result, title="Module 3 ReAct Agent Result"))

    if result.get("escalate"):
        print("\n🔴 ESCALATION REQUIRED — creating GitHub Issue body:")
        print(to_github_issue(result, module=3))
    else:
        print("\n✅ No escalation — agent produced a self-contained recommendation")

    return result


if __name__ == "__main__":
    main()
