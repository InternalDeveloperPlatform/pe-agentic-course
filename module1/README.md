# Module 1 — Platform Pain Points & The AI Opportunity

## What You Will Build

Your first Claude API call. A one-shot agent reads a CI failure log and returns structured JSON with a diagnosis — no loops, no tools, no multi-step reasoning. Just a system prompt, an API call, and clean structured output. This is the pattern every later module builds on.

---

## Files

| File | Purpose |
|------|---------|
| `verify_setup.py` | **Run this first** — pre-flight environment check |
| `hello_claude.py` | **Primary exercise script** — write your system prompt here |
| `agent.py` | Alternative entry point that saves output to file |
| `sample_log.txt` | Sample CI failure log (agent input) |
| `agent-config.yml` | Model and output schema |
| `solutions/solution.py` | Reference implementation — read after your own attempt |

---

## Step 1 — Verify Your Environment

Run this before anything else. It checks Python version, SDK installation, API key, and output directory.

```bash
python module1/verify_setup.py
```

**Expected output:**
```
✅ Python 3.11.x
✅ anthropic 0.x.x installed
✅ ANTHROPIC_API_KEY found
✅ output/ directory writable
Environment ready.
```

If a check fails, the message tells you exactly what to fix:
- Missing SDK → `pip install anthropic`
- Missing key → `export ANTHROPIC_API_KEY=sk-ant-...`

---

## Step 2 — Run the Agent

```bash
# See the expected output shape without an API key:
python module1/hello_claude.py --mock
```

**Expected output (mock mode):**
```json
{
  "summary": "3 test assertions failed in auth.test.js with memory climbing to 87%.",
  "likely_cause": "Uncleaned test fixtures retaining references between test cases, causing heap growth.",
  "next_step": "Add explicit cleanup in the afterEach hook and reduce fixture dataset size."
}
```

```bash
# Live call against Claude:
ANTHROPIC_API_KEY=sk-... python module1/hello_claude.py

# Saves full output to output/output_module1.json:
ANTHROPIC_API_KEY=sk-... python module1/agent.py
```

**Teaching point:** The system prompt is the program. Claude returns the same three keys every time because the system prompt specifies the exact JSON schema. This predictability is what makes agents composable.

---

## Exercise

Open `hello_claude.py`. Your task: write the `SYSTEM_PROMPT` that instructs Claude to return `summary`, `likely_cause`, and `next_step` in JSON, then call `ask()` with the contents of `sample_log.txt` as the user message.

Look at `agent-config.yml` for the expected output schema. Attempt your own implementation before reading `solutions/solution.py`.

---

## Success Criteria

- `verify_setup.py` reports all four checks green
- `hello_claude.py --mock` prints valid JSON with no parse errors
- Live run returns all three keys: `summary`, `likely_cause`, `next_step`
- Output saved to `output/output_module1.json`
