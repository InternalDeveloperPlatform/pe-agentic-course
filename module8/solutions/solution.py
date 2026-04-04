"""
module8/solutions/solution.py
Complete reference solution for Module 8 Capstone.

Only read this after you have attempted platform_agent.py yourself.

Run:
    python module8/solutions/solution.py --mock
    ANTHROPIC_API_KEY=sk-... python module8/solutions/solution.py --simulate
"""

import os
import sys
import json
import argparse
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from shared.claude_client import ask
from shared.output import save_json, to_step_summary, to_github_issue

MOCK_MODE = "--mock" in sys.argv or os.environ.get("MOCK_MODE") == "1"

# Re-use mock data and prompts from the student file
sys.path.insert(0, str(Path(__file__).parent.parent))
from platform_agent import (
    MOCK_REPORT,
    INGEST_PROMPT, DIAGNOSE_PROMPT, GATE_PROMPT,
    FIX_OR_ESCALATE_PROMPT, REPORT_PROMPT,
    AGENT_CONFIG, load_event, run_step, save_fix_script,
)


# ── Completed step functions ───────────────────────────────────────────────────

def run_step_ingest(event: dict) -> dict:
    return run_step("INGEST", INGEST_PROMPT, event)


def run_step_diagnose(event: dict, ingest: dict) -> dict:
    context = {
        "event":          event,
        "classification": ingest,
    }
    return run_step("DIAGNOSE", DIAGNOSE_PROMPT, context)


def run_step_gate(event: dict, diagnose: dict) -> dict:
    context = {
        "event":     event,
        "diagnosis": diagnose,
    }
    return run_step("GATE", GATE_PROMPT, context)


def run_step_fix_or_escalate(event: dict, diagnose: dict, gate: dict, pipeline_id: str) -> dict:
    context = {
        "event":     event,
        "diagnosis": diagnose,
        "gate":      gate,
    }
    result = run_step("FIX_OR_ESCALATE", FIX_OR_ESCALATE_PROMPT, context)

    if result.get("path") == "AUTO_FIX" and result.get("auto_fix_script"):
        fix_path = save_fix_script(result["auto_fix_script"], pipeline_id)
        result["fix_script_path"] = str(fix_path)

    return result


def generate_report(pipeline_id: str, steps: dict) -> dict:
    context = {
        "pipeline_id": pipeline_id,
        "steps":       steps,
    }
    return run_step("REPORT", REPORT_PROMPT, context)


# ── Orchestrator ───────────────────────────────────────────────────────────────

def run_pipeline(event: dict) -> dict:
    pipeline_id = event.get("pipeline_id", "unknown")
    steps = {}

    print("\n" + "═" * 60)
    print(f"PLATFORM AGENT (SOLUTION) — pipeline_id: {pipeline_id}")
    print("═" * 60)

    print("\n[Step 1/5] INGEST")
    steps["ingest"] = {**run_step_ingest(event), "status": "completed"}

    print("\n[Step 2/5] DIAGNOSE")
    steps["diagnose"] = {**run_step_diagnose(event, steps["ingest"]), "status": "completed"}

    print("\n[Step 3/5] GATE EVALUATION")
    steps["gate"] = {**run_step_gate(event, steps["diagnose"]), "status": "completed"}

    print("\n[Step 4/5] FIX OR ESCALATE")
    fix = run_step_fix_or_escalate(event, steps["diagnose"], steps["gate"], pipeline_id)
    steps["fix_or_escalate"] = {**fix, "status": "completed"}

    print("\n[Step 5/5] REPORT")
    steps["report"] = {**generate_report(pipeline_id, steps), "status": "completed"}

    return {
        "pipeline_id":   pipeline_id,
        "run_timestamp": datetime.now(timezone.utc).isoformat(),
        "steps":         steps,
        "final_output": {
            "recommended_action":  fix.get("recommended_action", "ESCALATE"),
            "escalate":            fix.get("escalate", True),
            "confidence":          steps["diagnose"].get("confidence", "LOW"),
            "github_issue_title":  fix.get("github_issue_title", ""),
            "github_issue_body":   fix.get("github_issue_body", ""),
            "post_mortem_summary": steps["report"].get("post_mortem_summary", ""),
        },
    }


def main():
    parser = argparse.ArgumentParser(description="Module 8 Capstone — Reference Solution")
    parser.add_argument("--simulate", action="store_true")
    parser.add_argument("--mock",     action="store_true")
    args = parser.parse_args()

    event = load_event(simulate=args.simulate)

    if MOCK_MODE:
        print("[MOCK MODE] Returning pre-defined pipeline report.\n")
        result = MOCK_REPORT
    else:
        result = run_pipeline(event)

    print("\n" + "═" * 60)
    print("FINAL REPORT")
    print("═" * 60)
    print(json.dumps(result, indent=2))

    save_json(result, module=8, label="solution")
    print(to_step_summary(result, title="Module 8 Solution"))

    final = result.get("final_output", {})
    if final.get("escalate"):
        print("\n🔴 ESCALATION REQUIRED")
        print(f"   Issue: {final.get('github_issue_title')}")
        print(to_github_issue(result, module=8))
    else:
        print("\n✅ Pipeline resolved — no escalation required.")


if __name__ == "__main__":
    main()
