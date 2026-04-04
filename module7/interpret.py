"""
module7/interpret.py
Developer Portal Interpreter — Module 7 Part B exercise script.

This script is the final step of the Part B exercise. It reads the orchestrator's
JSON output (from stdin or from the last saved output file) and uses Claude to:
  1. Convert the recommendation into a prioritised task list for the on-call team.
  2. Draft a one-paragraph "phased rollout memo" that a platform engineer can
     paste directly into Slack or a GitHub Issue.

Part B exercise usage (from mod7.js slide 16)
----------------------------------------------
    # Trigger the developer portal endpoint and pipe output through interpret.py:
    curl -s http://localhost:8080/portal/recommendations | python module7/interpret.py

    # Or run directly against the last orchestrator output:
    python module7/interpret.py

    # Mock mode (no API key):
    python module7/interpret.py --mock
    MOCK_MODE=1 python module7/interpret.py

What this script does
----------------------
1. Reads orchestrator JSON from stdin (if piped) or output/output_module7.json.
2. Calls Claude to convert the raw JSON into:
   - prioritised_tasks: ordered list of actions for the on-call team
   - rollout_memo: one paragraph suitable for Slack / GitHub Issue
   - recommended_action: DEPLOY | HOLD | ROLLBACK | ESCALATE
3. Prints the result and saves to output/output_module7_interpret.json.
"""

import os
import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from shared.claude_client import ask
from shared.output import save_json

# ── Mock mode ──────────────────────────────────────────────────────────────────
MOCK_MODE = "--mock" in sys.argv or os.environ.get("MOCK_MODE") == "1"

MOCK_RESPONSE = {
    "recommended_action": "ESCALATE",
    "prioritised_tasks": [
        "1. [IMMEDIATE] Page on-call engineer — open PagerDuty incident for INC-20847.",
        "2. [IMMEDIATE] Halt all pending deploys to checkout-service until root cause is confirmed.",
        "3. [5 min] Confirm rollback target: verify v1.8.2 image is available in ECR.",
        "4. [10 min] Execute rollback to v1.8.2 after human approval. Monitor error rate recovery.",
        "5. [Post-recovery] File post-mortem: identify why v1.9.0 cache warm-up was not caught in staging.",
        "6. [Next sprint] Add memory usage check to quality-gates.json — gate should block if startup memory > 80% of limit.",
    ],
    "rollout_memo": (
        "The Module 7 orchestrator detected a hard conflict between the Gate Agent (pre-deploy APPROVE) "
        "and the Rollback Agent (post-deploy IMMEDIATE rollback due to OOMKill and 18.4% P95 latency regression). "
        "Applying the Safety First policy: all pending deploys to checkout-service are on hold. "
        "Recommended action is to roll back to v1.8.2 immediately pending on-call engineer approval. "
        "Root cause is the cache warm-up introduced in v1.9.0 — 250k records loaded at startup exceeded the 512Mi memory limit. "
        "Fix path: increase memory limit to 2Gi OR implement lazy cache loading before re-deploying v1.9.0."
    ),
    "confidence": "HIGH",
}

# ── System prompt ──────────────────────────────────────────────────────────────
SYSTEM_PROMPT = """\
You are a developer portal interpreter agent. You receive the raw JSON output
from a multi-agent orchestrator and must translate it into clear, actionable
communication for a platform engineering team.

Return ONLY valid JSON with these keys:
- recommended_action (DEPLOY|HOLD|ROLLBACK|ESCALATE): single clear directive
- prioritised_tasks (list of strings): ordered action items, each starting with
  a priority label [IMMEDIATE], [5 min], [10 min], or [Post-recovery]
- rollout_memo (string): one paragraph (4–6 sentences) suitable for pasting into
  Slack or a GitHub Issue. Written in plain English for a mixed technical audience.
  Should cover: what happened, what the agent recommends, why, and the next step.
- confidence (HIGH|MEDIUM|LOW): confidence in the recommended action

Rules:
- If conflict.resolution contains SAFETY_FIRST or ESCALATE, recommended_action must be ESCALATE.
- prioritised_tasks must be ordered by urgency — most urgent first.
- rollout_memo must be one paragraph only — no bullet points, no headers.
- Never recommend DEPLOY if rollback_recommended=true in rollback_agent output.
"""


def load_orchestrator_output() -> dict:
    """Load orchestrator output from stdin or from the saved output file."""
    if not sys.stdin.isatty():
        data = sys.stdin.read().strip()
        if data:
            print("[interpret] Reading orchestrator output from stdin...", file=sys.stderr)
            return json.loads(data)

    # Fall back to last saved orchestrator output
    output_path = Path(__file__).parent.parent / "output" / "output_module7.json"
    if output_path.exists():
        print(f"[interpret] Reading from {output_path}", file=sys.stderr)
        return json.loads(output_path.read_text())

    # Fall back to sample_data if nothing else is available
    print("[interpret] No orchestrator output found — using sample_data.json", file=sys.stderr)
    sample = Path(__file__).parent / "sample_data.json"
    return json.loads(sample.read_text())


def run_interpreter(orchestrator_output: dict) -> dict:
    """Call Claude to interpret and communicate the orchestrator's output."""
    if MOCK_MODE:
        print("[interpret] [MOCK MODE] Returning pre-defined interpretation.")
        print("[interpret] Set ANTHROPIC_API_KEY and remove --mock to call the real API.\n")
        return MOCK_RESPONSE

    return ask(
        system=SYSTEM_PROMPT,
        user=f"Orchestrator output:\n\n{json.dumps(orchestrator_output, indent=2)}",
        max_tokens=1024,
    )


def main():
    orchestrator_output = load_orchestrator_output()

    print("\n[interpret] Interpreting orchestrator output...\n")
    result = run_interpreter(orchestrator_output)

    # Pretty print
    print("─" * 60)
    print(f"RECOMMENDED ACTION: {result.get('recommended_action', 'UNKNOWN')}")
    print("─" * 60)

    tasks = result.get("prioritised_tasks", [])
    if tasks:
        print("\nPRIORITISED TASKS:")
        for task in tasks:
            print(f"  {task}")

    memo = result.get("rollout_memo", "")
    if memo:
        print("\nROLLOUT MEMO (paste into Slack / GitHub Issue):")
        print("─" * 60)
        print(memo)
        print("─" * 60)

    # Save full result
    save_json(result, module=7, label="interpret")
    print(f"\n✅ Full result saved to output/output_module7_interpret.json")

    return result


if __name__ == "__main__":
    main()
