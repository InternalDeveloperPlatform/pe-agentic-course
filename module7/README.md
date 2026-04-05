# Module 7 — Multi-Agent Coordination and Implementation Strategy

## What You Will Build

A multi-agent orchestration system with two specialist agents running in parallel, a conflict-detection step, and a synthesis agent that produces a unified action plan:

- **`orchestrator.py`** — coordinates two specialist agents (FinOps Cost Optimizer + Incident Responder) running in parallel threads, detects conflicts between their outputs, and calls a synthesis agent to resolve them.
- **`interpret.py`** — reads the orchestrator's JSON output and uses Claude to convert it into a prioritised task list and a Slack-ready escalation memo.

---

## Files

| File | Purpose |
|------|---------|
| `orchestrator.py` | **Exercise file** — implement the three TODO functions |
| `interpret.py` | **Secondary script** — converts orchestrator output to human-readable format |
| `agent.py` | Simplified single-agent entry point |
| `sample_data.json` | Platform event with conflicting cost and incident signals |
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

## Run

```bash
# Mock mode — no API key needed:
python module7/orchestrator.py --mock

# Specific conflict scenario:
python module7/orchestrator.py --mock --scenario full_conflict
python module7/orchestrator.py --mock --scenario partial_conflict
python module7/orchestrator.py --mock --scenario no_conflict

# Live run against Claude (parallel specialist agents):
ANTHROPIC_API_KEY=sk-... python module7/orchestrator.py --scenario full_conflict

# Interpret the orchestrator's output (run after orchestrator):
python module7/interpret.py --mock
ANTHROPIC_API_KEY=sk-... python module7/interpret.py
```

---

## Architecture

```
Platform Event
     │
     ▼
 Orchestrator
     │
     ├──────────────────┐
     ▼                  ▼
Cost Optimizer    Incident Responder
(parallel)        (parallel)
     │                  │
     └──────────────────┘
             │
             ▼
      Conflict Check
             │
      ┌──────┴──────┐
      ▼             ▼
  No Conflict    Conflict
  → PROCEED    → ESCALATE
             │
             ▼
    Synthesis Agent
    (unified plan)
```

All messages flow through the orchestrator. Specialists never communicate with each other directly.

---

## Conflict Scenarios (from sample_data.json)

| Scenario | Cost Optimizer | Incident Responder | Outcome |
|----------|---------------|-------------------|---------|
| `no_conflict` | Scale down idle services | No active incident | PROCEED |
| `partial_conflict` | APPROVE_WITH_CONDITIONS | SCHEDULED rollback | Soft escalate |
| `full_conflict` | APPROVE | IMMEDIATE rollback | Hard escalate (Safety First) |

---

## Expected Output

```json
{
  "cost_optimizer": { "specialist": "cost_optimizer", "actions": ["scale_down: recommendation-service"], ... },
  "incident_responder": { "specialist": "incident_responder", "actions": ["investigate: checkout-service"], "protected_services": ["checkout-service", "payment-api"], ... },
  "synthesis": {
    "conflict_detected": true,
    "conflict_description": "No direct conflict — cost optimizer targets idle services only.",
    "unified_actions": ["scale_down: recommendation-service", "investigate: checkout-service"],
    "final_decision": "ESCALATE",
    "escalate": true
  }
}
```

Full result saved to `output/output_module7_unified_plan.json`.

---

## Exercise

**Part A — Orchestrator:** Open `orchestrator.py`. Implement the three TODO functions:

1. **`run_gate_agent(context)`** — call `ask()` with `GATE_SYSTEM_PROMPT` to evaluate quality gates
2. **`run_rollback_agent(context)`** — call `ask()` with `ROLLBACK_SYSTEM_PROMPT` to assess rollback need
3. **`detect_conflict(gate_result, rollback_result)`** — compare both outputs and return a conflict dict (HARD_CONFLICT / SOFT_CONFLICT / no conflict)

The specialists are already wired to run in parallel via `ThreadPoolExecutor` — you do not need to change `main()`.

```bash
python module7/orchestrator.py --mock --scenario full_conflict    # shows expected output
ANTHROPIC_API_KEY=sk-... python module7/orchestrator.py --scenario full_conflict
```

**Part B — Interpret:** Run `interpret.py` after the orchestrator to see the output converted into a human-readable escalation memo.

If you get stuck, see `solutions/solution.py`.

---

## Running agents safely

**Safety First** is the non-negotiable conflict resolution rule. When the Cost Optimizer recommends scaling down a service and the Incident Responder marks that same service as protected, the Incident Responder wins — always. Cost optimization is reversible; an outage during a live incident is not. The synthesis agent's job is not to find a compromise between the two specialists: it is to implement the Safety First rule and explain the reasoning. Notice that the `full_conflict` scenario produces `final_decision: ESCALATE` even when the conflict is technically resolvable — because the synthesis agent cannot verify the incident state in real time. Escalating is the correct and honest answer when the agent is uncertain about infrastructure safety.

---

## Success Criteria

- `orchestrator.py --mock` runs cleanly and shows all three scenarios
- Both specialist agents run and return valid JSON
- Conflict detection correctly identifies overlapping targets
- Synthesis agent produces `unified_actions` and `final_decision`
- `interpret.py` produces a readable task list and escalation memo
- Full output saved to `output/output_module7_unified_plan.json`
- If `escalate=true`, an escalation notice is printed
- If stuck, see `solutions/solution.py`
