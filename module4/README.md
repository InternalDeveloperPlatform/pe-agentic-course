# Module 4 — AI-Powered Diagnosis and Remediation

## What You Will Build

**Demo:** Push a deliberately broken app to CI. Watch the pipeline fail. Then run `diagnose.py` against the same logs and see it produce a structured diagnosis with line-level fix suggestions in under 10 seconds.

**Exercise:** Run `diagnose.py` against a harder failure — 33 integration tests fail, but the app code is unchanged. Root cause is a database migration lock. The key insight: `confidence: MEDIUM` + `escalate: true` is the *correct* answer when you are inferring infrastructure state rather than observing a deterministic code error.

---

## Files

| File | Purpose |
|------|---------|
| `triage_agent.py` | **Exercise file** — implement `run_agent()` |
| `diagnose.py` | Demo script — already complete, used for the NameError demo |
| `broken_app/app.py` | Deliberately broken app — two NameErrors. Used in the **demo**. Do not fix it. |
| `sample_migration_failure.json` | DB migration lock failure — **exercise input** |
| `sample_oomkill_event.json` | OOMKill K8s event — alternative scenario |
| `sample_data.json` | Silent 503 post-deploy scenario — additional reference |
| `agent-config.yml` | Model and output schema |
| `solutions/solution.py` | **Reference implementation** — read this only after your own attempt |

### GitHub Actions workflows

| Workflow | Trigger | Purpose |
|----------|---------|---------|
| `module4-broken-pipeline.yml` | Manual / push to `broken_app/**` | Runs the broken app → pipeline fails → agent diagnoses → creates GitHub Issue |
| `module4-triage-agent.yml` | Push to `module4/**` | Runs diagnose agent against sample data |

---

## Setup

```bash
export ANTHROPIC_API_KEY=your_key_here
python module1/verify_setup.py
```

---

## Demo — The Broken Pipeline

**Step 1 — Show the failure locally:**

```bash
python module4/broken_app/app.py
```

**Expected output:**
```
Traceback (most recent call last):
  File "module4/broken_app/app.py", line 37, in process_requests
    count += statis
NameError: name 'statis' is not defined
```

`broken_app/app.py` has two intentional NameErrors:
- Line 37: `count += statis` — `statis` was never declared (typo)
- Line 44: `version = app_version` — should be `APP_VERSION` (case mismatch)

**Step 2 — Run the diagnostic agent (mock mode first):**

```bash
python module4/diagnose.py --mock
```

**Expected output:**
```json
{
  "error_type": "NameError",
  "root_cause": "Two undefined variable references in broken_app/app.py. Bug 1 (line 37): 'statis' is referenced but never defined — likely a typo for a loop counter. Bug 2 (line 44): 'app_version' is used but the constant is named APP_VERSION (case mismatch).",
  "confidence": "HIGH",
  "fix": {
    "bug_1": {
      "file": "module4/broken_app/app.py",
      "line": 37,
      "original": "count += statis",
      "corrected": "count += 1"
    },
    "bug_2": {
      "file": "module4/broken_app/app.py",
      "line": 44,
      "original": "version = app_version",
      "corrected": "version = APP_VERSION"
    }
  },
  "post_mortem": {
    "what_happened": "CI pipeline failed with two NameErrors preventing the application from starting.",
    "why_it_happened": "A typo and a case mismatch introduced in the same commit. Python raises these at runtime.",
    "how_to_prevent": "Add a pre-commit hook running python -m py_compile on changed files."
  },
  "escalate": false
}
```

```bash
# Live call:
ANTHROPIC_API_KEY=sk-... python module4/diagnose.py
```

**Step 3 — Trigger the full GitHub Actions workflow:**

Actions → "Module 4 — Broken Pipeline (Demo)" → Run workflow. The diagnosis job appears within 5 seconds of the failure. The GitHub Issue is created automatically from the agent's JSON output.

**Teaching point:** `confidence: HIGH` here because NameErrors are deterministic — the log proves exactly what went wrong, line by line. Compare this with the exercise below.

---

## Exercise — DB Migration Lock Failure

Open `triage_agent.py`. The scenario is a silent 503 post-deploy failure — no exceptions, no code changes, just failing health checks. Implement `run_agent()`: write the `ask()` call that sends `SYSTEM_PROMPT` and the loaded context to Claude and returns the result dict.

```bash
python module4/triage_agent.py --mock                          # shows expected output
ANTHROPIC_API_KEY=sk-... python module4/triage_agent.py        # your live implementation
```

Also review `sample_migration_failure.json` — a second scenario (33 integration test failures from a DB migration lock). The teaching point is the same in both: MEDIUM confidence is correct when you are inferring infrastructure state.

**Expected output (migration lock scenario):**
```json
{
  "error_type": "MigrationTimeout",
  "root_cause": "33 integration tests failed post-deploy with no code defect. All failures are in the users table suite. A DB migration lock held by a prior deploy blocked schema changes from completing.",
  "confidence": "MEDIUM",
  "fix": {
    "action": "Clear the stale lock and re-run the migration before re-triggering CI",
    "verification": "Check pg_locks to confirm the lock is released before re-deploying"
  },
  "post_mortem": {
    "what_happened": "Schema migration timed out after 30 seconds while holding a table lock.",
    "why_it_happened": "A prior deploy left a lock that was never released. New migration could not acquire it.",
    "how_to_prevent": "Add migration lock timeout alerts. Verify lock release in post-deploy health check."
  },
  "escalate": true
}
```

**Why `confidence: MEDIUM`?** The agent sees the lock holder in the logs but cannot verify the lock was never released or confirm the prior deploy's state. It is inferring root cause from circumstantial evidence — not observing a deterministic error.

**Takeaway:** `confidence: MEDIUM` + `escalate: true` is the correct and honest answer. An agent that returns `HIGH` confidence on infrastructure state inference is more dangerous than one that escalates.

---

## Success Criteria

- `triage_agent.py --mock` runs without errors and prints valid JSON
- `diagnose.py --mock` also runs cleanly (demo script — already complete)
- **Demo (NameError):** `confidence: HIGH`, `escalate: false`, both bugs identified with corrected lines
- **Exercise (silent 503):** `confidence: MEDIUM`, `escalate: true` — state inference, not a deterministic error
- Full output saved to `output/output_module4.json`
- If stuck, see `solutions/solution.py`
