"""
module7/solutions/solution.py
Complete solution for Module 7 exercise: Multi-Agent Orchestrator with Parallel Agents

MOCK MODE: python module7/solutions/solution.py --mock
"""
import os, sys, json
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from shared.claude_client import ask
from shared.output import save_json, to_step_summary, to_github_issue

MOCK_MODE = "--mock" in sys.argv or os.environ.get("MOCK_MODE") == "1"

MOCK_COST_OPTIMIZER = {
    "specialist": "cost_optimizer",
    "actions": ["scale_down: recommendation-service (idle >4h)", "scale_down: batch-processor (queue empty)"],
    "protected_services": [],
    "confidence": "HIGH",
}

MOCK_INCIDENT_RESPONDER = {
    "specialist": "incident_responder",
    "actions": ["investigate: checkout-service (error rate +22%)", "alert: on-call engineer"],
    "protected_services": ["checkout-service", "payment-api"],
    "confidence": "HIGH",
}

MOCK_SYNTHESIS = {
    "conflict_detected": True,
    "conflict_description": "No direct conflict — cost optimizer targets idle services, incident responder protects checkout-service. Actions are compatible.",
    "unified_actions": [
        "scale_down: recommendation-service",
        "scale_down: batch-processor",
        "investigate: checkout-service",
        "alert: on-call engineer"
    ],
    "final_decision": "ESCALATE",
    "escalation_reason": "checkout-service error rate spike requires human decision on rollback before any further scaling actions.",
    "escalate": True,
}

COST_SYSTEM = "You are a FinOps Cost Optimizer agent. Return ONLY valid JSON: specialist (string), actions (list), protected_services (list), confidence (HIGH|MEDIUM|LOW)."
INCIDENT_SYSTEM = "You are an Incident Responder agent. Return ONLY valid JSON: specialist (string), actions (list), protected_services (list), confidence (HIGH|MEDIUM|LOW)."
SYNTHESIS_SYSTEM = "You are a synthesis agent. Given two specialist reports, detect conflicts and produce a unified plan. Return ONLY valid JSON: conflict_detected (boolean), conflict_description (string), unified_actions (list), final_decision (PROCEED|ESCALATE), escalation_reason (string), escalate (boolean)."

def run_specialist(name: str, system: str, context: str, mock_response: dict) -> dict:
    if MOCK_MODE:
        print(f"[MOCK MODE] {name} returning pre-defined response.")
        return mock_response
    return ask(system=system, user=f"Context:\n{context}", max_tokens=1024)

def run():
    sample = (Path(__file__).parent.parent / "sample_data.json").read_text()

    # Run both specialists in parallel
    print("\n[ORCHESTRATOR] Running Cost Optimizer and Incident Responder in parallel...")
    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = {
            executor.submit(run_specialist, "CostOptimizer", COST_SYSTEM, sample, MOCK_COST_OPTIMIZER): "cost",
            executor.submit(run_specialist, "IncidentResponder", INCIDENT_SYSTEM, sample, MOCK_INCIDENT_RESPONDER): "incident",
        }
        results = {}
        for future in as_completed(futures):
            key = futures[future]
            results[key] = future.result()
            print(f"\n[{key.upper()}] {json.dumps(results[key], indent=2)}")

    # Conflict detection
    overlap = set(results["cost"].get("actions", [])) & set(results["incident"].get("protected_services", []))
    print(f"\n[CONFLICT CHECK] Overlapping targets: {overlap or 'none'}")

    # Synthesis
    print("\n[SYNTHESIS] Running synthesis agent...")
    synthesis_input = json.dumps({"cost_optimizer": results["cost"], "incident_responder": results["incident"]}, indent=2)
    if MOCK_MODE:
        synthesis = MOCK_SYNTHESIS
        print("[MOCK MODE] Synthesis returning pre-defined response.")
    else:
        synthesis = ask(system=SYNTHESIS_SYSTEM, user=f"Agent outputs:\n{synthesis_input}", max_tokens=1024)

    print("\n[SYNTHESIS RESULT]"); print(json.dumps(synthesis, indent=2))

    output = {"cost_optimizer": results["cost"], "incident_responder": results["incident"], "synthesis": synthesis}
    save_json(output, module=7, label="unified_plan")
    print(to_step_summary(synthesis, "Module 7 Orchestrator Result"))
    if synthesis.get("escalate"):
        print("\n🔴 ESCALATION REQUIRED"); print(to_github_issue(synthesis, module=7))
    return output

if __name__ == "__main__":
    run()
