"""
module3/solutions/solution.py
Reference solution for Module 3: ReAct Loop Agent.

What this module teaches
------------------------
The ReAct (Reason + Act) pattern: an agent that iterates — reasoning about
the current state, deciding on an action, receiving an observation, then
deciding whether it has enough information to produce a final answer.

Key insight: the loop exits when finished=True, not when max_iterations is
reached. max_iterations is a safety ceiling only. An agent that always runs
to the maximum is not reasoning — it is looping.

The loop is built by feeding the previous iterations back as history in the
next user message. This gives Claude the full context of what it has already
tried, preventing it from repeating the same action and enabling it to reason
about progress across iterations.

Compare with: module3/agent.py (the exercise you completed)

Run
---
    python module3/solutions/solution.py --mock     # shows a single finished iteration
    ANTHROPIC_API_KEY=sk-... python module3/solutions/solution.py
"""

import os
import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from shared.claude_client import ask
from shared.output import save_json, to_step_summary, to_github_issue

# ── Mock mode ──────────────────────────────────────────────────────────────────
MOCK_MODE = "--mock" in sys.argv or os.environ.get("MOCK_MODE") == "1"

# Mock shows a single completed iteration (finished=True) so you can see the
# final output shape without waiting for Claude to iterate.
MOCK_RESPONSE = {
    "thought": (
        "The pod is in CrashLoopBackOff with exit code 137. "
        "Exit code 137 is SIGKILL — the kernel OOM killer terminated the process. "
        "The restart count of 8 in 22 minutes confirms repeated kills, not an application crash."
    ),
    "action": (
        "Check memory requests/limits in the pod spec and compare against "
        "actual peak usage reported before the kill."
    ),
    "observation": (
        "Pod requests 512Mi and limit is 512Mi. Peak usage before kill was 1.2Gi. "
        "The memory limit is 2.3x too low for peak load. No code change in this deploy."
    ),
    "finished": True,
    "confidence": "HIGH",
    "recommended_action": (
        "kubectl patch deployment checkout-api -p "
        "'{\"spec\":{\"template\":{\"spec\":{\"containers\":"
        "[{\"name\":\"checkout-api\",\"resources\":{\"limits\":{\"memory\":\"2Gi\"}}}]}}}}'"
    ),
    "escalate": False,
}

# ── System prompt ──────────────────────────────────────────────────────────────
# This prompt defines the ReAct contract: every response must include all
# seven keys. finished=True is the exit signal; the orchestrator checks it
# after each iteration.
SYSTEM_PROMPT = (
    "You are a ReAct-pattern Kubernetes incident analysis agent. "
    "For EACH iteration return ONLY valid JSON with ALL of these keys:\n"
    "  thought           (string) — your reasoning about the current state\n"
    "  action            (string) — what you want to investigate next\n"
    "  observation       (string) — what the action reveals\n"
    "  finished          (boolean) — true when you have enough to recommend a fix\n"
    "  confidence        (HIGH|MEDIUM|LOW) — meaningful only when finished=true\n"
    "  recommended_action (string) — the specific fix command (only when finished=true)\n"
    "  escalate          (boolean) — true if human review is required\n"
    "Stop iterating as soon as you have enough evidence. "
    "Do not run to max_iterations if the answer is already clear."
)

AGENT_CONFIG = {
    "model":          "claude-opus-4-5-20251101",
    "max_tokens":     1024,
    "max_iterations": 5,
}


def load_sample() -> str:
    """Load the K8s OOMKill incident data from sample_data.json."""
    return (Path(__file__).parent.parent / "sample_data.json").read_text()


def run_agent() -> dict:
    """
    ReAct loop: iterate until finished=True or max_iterations is reached.

    History pattern
    ---------------
    On the first iteration Claude sees only the raw incident data.
    On each subsequent iteration, the full history of all previous iterations
    is appended to the user message so Claude can see what it has already tried.
    This prevents repeated actions and lets Claude reason about progress.

    The loop structure:
        for i in range(max_iterations):
            user_msg = incident + (history if i > 0)
            result = ask(system, user_msg)
            history.append(result)
            if result["finished"]: break
    """
    incident = load_sample()

    if MOCK_MODE:
        print("[MOCK MODE] Skipping Claude API — returning single completed iteration.")
        print("[MOCK MODE] In real mode, the loop runs up to 5 times.\n")
        result = MOCK_RESPONSE
        print("[Iteration 1 — FINISHED]")
        print(json.dumps(result, indent=2))
    else:
        history = []
        result  = {}

        for i in range(AGENT_CONFIG["max_iterations"]):
            # First call: just the incident. Subsequent calls: incident + full history.
            # Passing the complete history (not just the last step) lets Claude see
            # the full investigative trajectory and avoid repeating actions.
            if history:
                user_msg = (
                    f"Incident:\n{incident}\n\n"
                    f"Previous iterations:\n{json.dumps(history, indent=2)}"
                )
            else:
                user_msg = f"Incident:\n{incident}"

            result = ask(
                system=SYSTEM_PROMPT,
                user=user_msg,
                model=AGENT_CONFIG["model"],
                max_tokens=AGENT_CONFIG["max_tokens"],
            )

            print(f"\n[Iteration {i + 1}{'  — FINISHED' if result.get('finished') else ''}]")
            print(json.dumps(result, indent=2))

            history.append(result)

            # Exit as soon as Claude signals it has enough information.
            # This is the key ReAct property: the agent decides when to stop.
            if result.get("finished"):
                print(f"\n[Loop exited after {i + 1} iteration(s) — finished=True]")
                break
        else:
            # Safety net: loop exhausted without finished=True
            print(f"\n[Loop reached max_iterations={AGENT_CONFIG['max_iterations']} — using last result]")

    print(json.dumps(result, indent=2))
    save_json(result, module=3)
    print(to_step_summary(result, title="Module 3 Agent Result"))

    if result.get("escalate"):
        print("\n🔴 ESCALATION REQUIRED — GitHub Issue body:")
        print(to_github_issue(result, module=3))
    else:
        print("\n✅ No escalation — agent produced a self-contained recommendation")

    return result


if __name__ == "__main__":
    run_agent()
