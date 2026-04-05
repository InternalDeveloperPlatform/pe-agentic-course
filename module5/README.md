# Module 5 — Intelligent CI/CD and Adaptive Delivery

## What You Will Build

A two-agent CI/CD quality gate system:

1. **`triage_agent.py`** (blocking gate) — runs *before* deploy, evaluates the release candidate against six configurable thresholds in `quality-gates.json`, and returns `APPROVE`, `APPROVE_WITH_CONDITIONS`, or `HOLD`.
2. **`monitor.py`** (post-deploy watchdog) — runs *after* deploy on a timed check, evaluates live production signals, and decides whether to recommend an immediate rollback.

This is deliberate separation of concerns: the gate prevents bad deploys; the monitor catches what slips through.

---

## Files

| File | Purpose |
|------|---------|
| `triage_agent.py` | **Exercise file** — implement `run_agent()` for the pre-deploy gate |
| `monitor.py` | **Exercise file** — implement `run_agent()` for the post-deploy monitor |
| `quality-gates.json` | Threshold configuration (edit this to change gate behaviour) |
| `sample_data.json` | Sample pipeline results (agent input for both scripts) |
| `agent-config.yml` | Model and output schema |
| `solutions/solution.py` | **Reference implementation** — read this only after your own attempt |

---

## Setup

```bash
# From the repo root
export ANTHROPIC_API_KEY=your_key_here
python module1/verify_setup.py
```

---

## Run the Quality Gate Agent

```bash
# Mock mode — see expected output shape:
python module5/triage_agent.py --mock

# Live call (evaluates sample_data.json against quality-gates.json):
ANTHROPIC_API_KEY=sk-... python module5/triage_agent.py
```

## Run the Post-Deploy Monitor

```bash
# Mock mode:
python module5/monitor.py --mock

# Live call:
ANTHROPIC_API_KEY=sk-... python module5/monitor.py
```

---

## Quality Gates (from quality-gates.json)

| Gate | Metric | Threshold | Blocks Deploy? |
|------|--------|-----------|----------------|
| Unit Test Coverage | `coverage_pct` | ≥ 95% | No |
| Branch Coverage | `coverage_branch_pct` | ≥ 80% | No |
| SAST High Findings | `security_scan.high` | = 0 | **Yes** |
| Lighthouse Score | `lighthouse_score` | ≥ 85 | No |
| P95 Latency Delta | `latency_p95_delta_pct` | ≤ 10% | **Yes** |
| Cost Per Request Delta | `cost_per_request_delta_pct` | ≤ 10% | No |

Edit `quality-gates.json` to adjust thresholds without changing any code.

---

## Expected Output (Quality Gate — borderline case)

```json
{
  "decision": "APPROVE_WITH_CONDITIONS",
  "confidence": "HIGH",
  "rationale": "All critical gates pass. Coverage 74.1% is below threshold but has not regressed. Friday deploy window elevates risk.",
  "blocking_issues": [],
  "conditions": [
    "Coverage must not regress below 74% in the next three PRs",
    "Deploy should target off-peak hours (before 14:00 UTC)"
  ],
  "risk_score": "MEDIUM",
  "recommended_deploy_window": "Before 14:00 UTC today or defer to Monday",
  "escalate": false
}
```

Full result saved to `output/output_module5.json`.

---

## Exercise

**Part A — Quality gate:** Open `triage_agent.py`. Implement `run_agent()` — write the `ask()` call that sends `SYSTEM_PROMPT` and the pipeline results to Claude and returns the result dict. The `SYSTEM_PROMPT` is already written for you; study it before calling `ask()`.

```bash
python module5/triage_agent.py --mock                          # shows expected output
ANTHROPIC_API_KEY=sk-... python module5/triage_agent.py        # your live implementation
```

**Part B — Threshold experiment:** Lower the `threshold` for `test_coverage` in `quality-gates.json` from 95 to 70. Re-run `triage_agent.py` and observe how the decision changes — no code edit needed, just the config file.

If you get stuck, see `solutions/solution.py` for the reference implementation.

---

## Multiple failure modes

The gate and the monitor are intentionally two separate agents with two separate failure modes. The gate is **preventive** — it blocks a bad deploy before it reaches production. The monitor is **reactive** — it catches the failures that slip through. A single agent trying to do both jobs would conflate pre-deploy reasoning (static analysis of pipeline results) with post-deploy reasoning (live production signals). Keeping them separate also means you can tune each agent's confidence threshold and system prompt independently. The monitor's `rollback_recommended` decision is a different kind of judgment than the gate's `decision` — one is about risk, the other is about live impact.

---

## Success Criteria

- `triage_agent.py --mock` runs cleanly and shows expected output shape
- Live run returns `decision` of APPROVE, APPROVE_WITH_CONDITIONS, or HOLD
- `monitor.py` returns `rollback_recommended` (boolean) with a `severity`
- Editing `quality-gates.json` changes the gate decision without code changes
- Full output saved to `output/output_module5.json`
- If stuck, see `solutions/solution.py`
