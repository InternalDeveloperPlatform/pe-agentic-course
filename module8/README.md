# Module 8 — Capstone: Build Your Production Platform Agent

This is the final module. You complete a real 5-step pipeline agent that diagnoses CI failures, evaluates quality gates, decides whether to auto-fix or escalate, and writes a structured post-mortem — all without human involvement.

---

## How the Capstone Works

Open `module8/platform_agent.py`. Step 1 (INGEST) is fully implemented as a worked example — read it, then complete Steps 2–5 by implementing the four TODO functions and run the full pipeline yourself.

**Budget: ~45 minutes.**

---

## The Pipeline

| Step | Function to complete | What Claude does |
|------|----------------------|------------------|
| 1 | `run_step_ingest()` | Classifies the failure event — **already done, use as your pattern** |
| 2 | `run_step_diagnose()` | Root cause analysis — confidence HIGH/MEDIUM/LOW, fix_possible true/false |
| 3 | `run_step_gate()` | Quality gate evaluation — APPROVE, APPROVE_WITH_CONDITIONS, or HOLD |
| 4 | `run_step_fix_or_escalate()` | Branching logic — AUTO_FIX or ESCALATE + save fix script if applicable |
| 5 | `generate_report()` | Post-mortem summary and prevention recommendations |

The pipeline orchestrator (`run_pipeline()`) is already wired up and calls your functions in order. Do not edit it.

---

## Setup

```bash
# From the repo root
export ANTHROPIC_API_KEY=your_key_here
python module1/verify_setup.py
```

---

## Step-by-Step Instructions

### Step 1 — Run mock mode first

Before writing any code, run the agent in mock mode to see the shape of each step's output:

```bash
python module8/platform_agent.py --simulate --mock
```

You will see five JSON blocks — INGEST, DIAGNOSE, GATE, FIX/ESCALATE, REPORT — followed by the final report and a 🔴 ESCALATION message. This is exactly what your completed functions will produce.

### Step 3 — Read the worked example

Open `platform_agent.py` and read `run_step_ingest()` carefully. Every other step follows the same three-line pattern:

```python
def run_step_ingest(event: dict) -> dict:
    return run_step("INGEST", INGEST_PROMPT, event)
```

The difference for Steps 2–5 is that you need to build a richer `context` dict that passes results from earlier steps to Claude.

### Step 6 — Complete `run_step_diagnose()`

Build a context dict that contains both the original `event` and the `ingest` result, then call `run_step()` with `DIAGNOSE_PROMPT`.

```python
def run_step_diagnose(event: dict, ingest: dict) -> dict:
    context = {
        "event":          event,
        "classification": ingest,   # gives Claude the step 1 output
    }
    return run_step("DIAGNOSE", DIAGNOSE_PROMPT, context)
```

Run after completing this step:

```bash
python module8/platform_agent.py --simulate --mock
```

Mock mode skips the real TODO steps — but once you implement DIAGNOSE, remove `--mock` to verify Step 2 calls Claude correctly before continuing:

```bash
ANTHROPIC_API_KEY=sk-... python module8/platform_agent.py --simulate
```

### Step 7 — Complete `run_step_gate()`

Same pattern. Context combines `event` and `diagnose` result.

### Step 8 — Complete `run_step_fix_or_escalate()`

This step has the key branching logic. After calling `run_step()`:

- If `result['path'] == 'AUTO_FIX'` and `result.get('auto_fix_script')` is non-empty → call `save_fix_script(result['auto_fix_script'], pipeline_id)` and add the returned path to `result['fix_script_path']`.
- Otherwise return the result as-is (ESCALATE path).

The AUTO_FIX path only triggers when the system prompt conditions are all met (HIGH confidence + fix_possible=true + no DB migration involved). For the default `--simulate` event, the expected result is ESCALATE.

### Step 9 — Complete `generate_report()`

Build context from `pipeline_id` and the full `steps` dict, call `run_step()` with `REPORT_PROMPT`.

### Step 8 — Run the full pipeline live

```bash
ANTHROPIC_API_KEY=sk-... python module8/platform_agent.py --simulate
```

All five steps should complete, each printing a JSON block. The final output will show either 🔴 ESCALATION REQUIRED or ✅ Pipeline resolved.

### Step 9 — Trigger via GitHub Actions

Push any commit to your fork to trigger the workflow manually, or use the Actions tab → "Module 8 — Capstone Agent" → "Run workflow".

The workflow also fires automatically if the `module4-broken-pipeline` workflow fails in your repo.

Check: Actions tab → select the run → verify the Step Summary tab shows the report and the artifact `module8-capstone-report` is attached.

---

## Your Deliverable — A 2–3 Minute Screen Recording

Record your screen while running the live pipeline. The video proves the agent ran (Claude's reasoning is visible, the pipeline_id is unique to your run) and is a portfolio artifact you can share in any engineering interview or team demo. No editing required.

**What to show in the recording:**

1. **Your code** — open `platform_agent.py` briefly and point to one completed TODO function.
2. **Mock mode** — run this so the 5-step structure is visible before the live run:
   ```bash
   python module8/platform_agent.py --simulate --mock
   ```
3. **Live run** — let all five steps stream in real time:
   ```bash
   ANTHROPIC_API_KEY=sk-... python module8/platform_agent.py --simulate
   ```
4. **The output file** — open `output/output_module8_platform_agent.json` and scroll through it to show Claude's verbatim reasoning for each step.
5. **GitHub Actions** — open the Actions tab in your browser and show the completed workflow run with the Step Summary visible.

---

## Expected Output

```
════════════════════════════════════════════════════════════
PLATFORM AGENT — pipeline_id: sim-20260403-142200
════════════════════════════════════════════════════════════

[Step 1/5] INGEST
── Step: INGEST ──────────────────────────────────────────
{ "event_type": "CI_FAILURE", "service": "platform-service",
  "failure_stage": "integration-tests", "severity": "P2", ... }

[Step 2/5] DIAGNOSE
── Step: DIAGNOSE ─────────────────────────────────────────
{ "error_type": "MigrationLockTimeout",
  "confidence": "MEDIUM", "fix_possible": false, ... }

[Step 3/5] GATE EVALUATION
── Step: GATE ─────────────────────────────────────────────
{ "decision": "HOLD", "risk_score": "HIGH", "escalate": true, ... }

[Step 4/5] FIX OR ESCALATE
── Step: FIX_OR_ESCALATE ─────────────────────────────────
{ "path": "ESCALATE", "github_issue_title": "[Agent] ...", ... }

[Step 5/5] REPORT
── Step: REPORT ───────────────────────────────────────────
{ "post_mortem_summary": "...", "recommendations": [...] }

════════════════════════════════════════════════════════════
PLATFORM AGENT — FINAL REPORT
════════════════════════════════════════════════════════════

🔴 ESCALATION REQUIRED
   Action : ESCALATE
   Issue  : [Agent] DB Migration Lock Blocking Integration Tests — Manual Intervention Required
```

**Files written:**

| File | Contents |
|------|----------|
| `output/output_module8_platform_agent.json` | Full structured report — all 5 steps + final_output |
| `module8/fixes/fix_<pipeline_id>.py` | Auto-fix script (only written on AUTO_FIX path) |

---

## Teaching Point

The student skeleton is intentional. Step 1 (INGEST) is fully implemented so you can see the exact three-line pattern before writing any code yourself. Steps 2–5 are `raise NotImplementedError` stubs — not because the code is hard, but because the pattern is simple enough that writing it four more times ingrains it. Every production platform agent you build after this course will follow the same pattern: build a context dict, call Claude with a system prompt, parse structured JSON output, pass the result to the next step. The capstone is proving you understand the pattern well enough to replicate it — not that you can write complex code. The recording deliverable exists for the same reason: a 2-minute video of a live pipeline run is something you can show in an interview to demonstrate you built something real.

---

## Success Criteria

- All five steps complete and print JSON to the terminal without errors.
- `output/output_module8_platform_agent.json` is written and contains all five steps plus `final_output`.
- ESCALATE path: `final_output.github_issue_title` and `github_issue_body` are non-empty strings.
- AUTO_FIX path (optional — requires editing `sample_data.json` to a HIGH confidence scenario): a fix script appears in `module8/fixes/`.
- GitHub Actions workflow completes and the Step Summary is visible in the Actions UI.

---

## Troubleshooting

**`NotImplementedError: Complete run_step_diagnose()`**
You haven't implemented that step yet. Follow the pattern from `run_step_ingest()` — build a context dict and call `run_step()`.

**`ModuleNotFoundError: No module named 'shared'`**
Run from the repo root, not from inside `module8/`:
```bash
# Correct
python module8/platform_agent.py --mock

# Wrong
cd module8 && python platform_agent.py --mock
```

**`JSONDecodeError` in a pipeline step**
Claude returned text that wasn't valid JSON. Check the system prompt constant for that step — it must contain "Return ONLY valid JSON". You can also add `print(raw_response)` before the parse in `shared/claude_client.py` to see what Claude actually returned.

**Step 4 always takes ESCALATE even with HIGH confidence**
Check that your `run_step_fix_or_escalate()` passes the `diagnose` result in the context dict. If Claude doesn't see `fix_possible: true` and `confidence: HIGH` in the context, it will default to ESCALATE.

**GitHub Actions workflow does not appear**
The workflow file must be on your default branch. Push your changes to `main` first, then the workflow becomes available in the Actions tab.

**`ANTHROPIC_API_KEY` secret not found in Actions**
Go to your repo → Settings → Secrets and variables → Actions → New repository secret. Name it `ANTHROPIC_API_KEY`.

---

## Files

| File | Purpose |
|------|---------|
| `platform_agent.py` | **Exercise file** — Step 1 is complete; implement Steps 2–5 |
| `sample_data.json` | Sample CI failure event (used when `--simulate` is not set) |
| `agent-config.yml` | Agent configuration (model, thresholds) |
| `solutions/solution.py` | **Reference implementation** — only read after attempting your own |
| `fixes/` | Auto-fix scripts are saved here on AUTO_FIX path |
