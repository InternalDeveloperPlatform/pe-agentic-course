"""
module3/solutions/solution.py
Complete solution for Module 3 exercise: ReAct Loop for K8s CrashLoopBackOff

MOCK MODE: python module3/solutions/solution.py --mock
"""
import os, sys, json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from shared.claude_client import ask
from shared.output import save_json, to_step_summary, to_github_issue

MOCK_MODE = "--mock" in sys.argv or os.environ.get("MOCK_MODE") == "1"

MOCK_RESPONSE = {
    "thought": "The pod is in CrashLoopBackOff with exit code 137. Exit code 137 is SIGKILL — the OOM killer terminated the process.",
    "action": "Check memory requests/limits in the pod spec against actual peak usage.",
    "observation": "Pod requests 512Mi but actual peak usage was 1.2Gi. The memory limit is causing repeated OOM kills.",
    "finished": True,
    "confidence": "HIGH",
    "recommended_action": 'kubectl patch deployment checkout-api -p \'{"spec":{"template":{"spec":{"containers":[{"name":"checkout-api","resources":{"limits":{"memory":"2Gi"}}}]}}}}\'',
    "escalate": False,
}

SYSTEM_PROMPT = (
    "You are a ReAct-pattern Kubernetes incident analysis agent. "
    "For each iteration return ONLY valid JSON with keys: thought (string), action (string), "
    "observation (string), finished (boolean), confidence (HIGH|MEDIUM|LOW), "
    "recommended_action (string, only when finished=true), escalate (boolean)."
)

TOOLS = {
    "describe_pod": lambda pod: f"Pod {pod}: restartCount=8, exitCode=137, lastState=OOMKilled, memory.requests=512Mi, memory.limits=512Mi",
    "check_memory": lambda pod: f"Peak memory before kill: 1.2Gi. Current limit: 512Mi. Recommendation: increase limit to 2Gi.",
    "get_logs": lambda pod: f"Last 20 lines before kill: [heap allocation failed, js stack overflow], process exited with signal 9 (SIGKILL)",
}

def run():
    sample = (Path(__file__).parent.parent / "sample_data.json").read_text()

    if MOCK_MODE:
        print("[MOCK MODE] Skipping Claude API — showing single completed ReAct iteration.\n")
        result = MOCK_RESPONSE
        print(json.dumps(result, indent=2))
    else:
        history = []
        result = {}
        for i in range(5):
            context = f"Incident:\n{sample}\n\nHistory:\n{json.dumps(history, indent=2)}" if history else f"Incident:\n{sample}"
            result = ask(system=SYSTEM_PROMPT, user=context, max_tokens=1024)
            print(f"\n[Iteration {i+1}]"); print(json.dumps(result, indent=2))
            history.append(result)
            if result.get("finished"):
                break

    save_json(result, module=3)
    print(to_step_summary(result, "Module 3 Agent Result"))
    if result.get("escalate"):
        print("\n🔴 ESCALATION REQUIRED"); print(to_github_issue(result, module=3))
    return result

if __name__ == "__main__":
    run()
