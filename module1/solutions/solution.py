"""
module1/solutions/solution.py
Complete solution for Module 1 exercise: Hello Agent

MOCK MODE: python module1/solutions/solution.py --mock
"""
import os, sys, json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from shared.claude_client import ask
from shared.output import save_json, to_step_summary

MOCK_MODE = "--mock" in sys.argv or os.environ.get("MOCK_MODE") == "1"

MOCK_RESPONSE = {
    "summary": "The Node.js test suite failed with 3 assertions failing in auth.test.js. Memory usage climbed to 87% during the run.",
    "likely_cause": "Uncleaned test fixtures are retaining references between test cases, causing heap growth and eventual assertion failures.",
    "next_step": "Add explicit cleanup in the afterEach hook for auth.test.js and reduce fixture dataset size.",
}

SYSTEM_PROMPT = (
    "You are a platform engineering assistant. "
    "Analyse the log snippet and return ONLY valid JSON with keys: "
    "summary (string), likely_cause (string), next_step (string)."
)

def run():
    log = (Path(__file__).parent.parent / "sample_log.txt").read_text()
    if MOCK_MODE:
        print("[MOCK MODE] Skipping Claude API.\n")
        result = MOCK_RESPONSE
    else:
        result = ask(system=SYSTEM_PROMPT, user=f"Log:\n{log}", max_tokens=512)
    print(json.dumps(result, indent=2))
    save_json(result, module=1)
    print(to_step_summary(result, "Module 1 Agent Result"))
    return result

if __name__ == "__main__":
    run()
