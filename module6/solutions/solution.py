"""
module6/solutions/solution.py
Complete solution for Module 6 exercise: Conversational Observability REPL

MOCK MODE: python module6/solutions/solution.py --mock
"""
import os, sys, json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from shared.claude_client import ask
from shared.output import save_json, to_step_summary

MOCK_MODE = "--mock" in sys.argv or os.environ.get("MOCK_MODE") == "1"

MOCK_RESPONSE = {
    "answer": "The checkout-service is experiencing elevated latency (p95 = 2.3s vs 0.4s baseline). This started at 14:32 UTC, 8 minutes after the last deployment. The payment-api dependency is showing a 40% error rate which is the most likely cause.",
    "causal_chain": [
        "checkout-service deployment completed at 14:24 UTC",
        "payment-api error rate began rising at 14:32 UTC (8-minute lag)",
        "checkout-service latency spiked as retries accumulated against failing payment-api",
        "downstream: cart-service timeout rate increased as checkout responses slowed"
    ],
    "confidence": "MEDIUM",
    "follow_up_questions": [
        "Was there a simultaneous change to payment-api at or before 14:32 UTC?",
        "What does the payment-api error response body contain — rate limit, timeout, or 5xx?"
    ],
    "escalate": True,
}

SYSTEM_PROMPT = (
    "You are a conversational platform observability agent. "
    "Receive live metrics and a natural-language question. "
    "Return ONLY valid JSON: answer (string, max 3 sentences), "
    "causal_chain (list of strings), confidence (HIGH|MEDIUM|LOW), "
    "follow_up_questions (list of 2 strings), escalate (boolean)."
)

def ask_agent(snapshot: str, question: str) -> dict:
    if MOCK_MODE:
        return MOCK_RESPONSE
    return ask(system=SYSTEM_PROMPT, user=f"Metrics snapshot:\n{snapshot}\n\nQuestion: {question}", max_tokens=1024)

def run():
    snapshot = (Path(__file__).parent.parent / "sample_data.json").read_text()

    if MOCK_MODE:
        print("[MOCK MODE] Single-shot mock response (real mode runs interactive REPL).\n")
        result = ask_agent(snapshot, "What is causing the latency spike?")
        print(json.dumps(result, indent=2))
        save_json(result, module=6)
        return result

    # Interactive REPL loop
    print("Platform Observability Agent — type your question (or 'exit' to quit)\n")
    result = {}
    while True:
        try:
            question = input("Question> ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if question.lower() in ("exit", "quit", ""):
            break
        result = ask_agent(snapshot, question)
        print("\n" + json.dumps(result, indent=2) + "\n")

    if result:
        save_json(result, module=6)
        print(to_step_summary(result, "Module 6 Agent Result"))
    return result

if __name__ == "__main__":
    run()
