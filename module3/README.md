# Module 3 — Agents That Think: ReAct & Planning

## What You Will Build

A ReAct-pattern agent that investigates a Kubernetes CrashLoopBackOff across multiple iterations. Each loop: Claude reasons about the incident, decides on an action, receives an observation, and decides whether it has enough information to finish. The loop exits when `finished=true` or `max_iterations` is reached.

---

## Files

| File | Purpose |
|------|---------|
| `agent.py` | **Exercise file** — implement the ReAct loop in `run_agent()` |
| `hello_agent.py` | Complete worked example with `--scenario` flag — read after implementing |
| `sample_data.json` | OOMKill K8s event (agent input) |
| `sample_k8s_event.json` | Alternative OOMKill scenario for experimentation |
| `agent-config.yml` | Model, max_iterations, and output schema |
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
# Mock mode — shows a completed single-iteration ReAct response:
python module3/agent.py --mock

# Live multi-step loop (up to 5 iterations):
ANTHROPIC_API_KEY=sk-... python module3/agent.py

# Full run that saves to output/output_module3.json:
ANTHROPIC_API_KEY=sk-... python module3/agent.py
```

---

## How the ReAct Loop Works

Each iteration, Claude returns JSON with these keys:

| Key | Type | Meaning |
|-----|------|---------|
| `thought` | string | Claude's reasoning about the current state |
| `action` | string | What Claude wants to investigate next |
| `observation` | string | What the action reveals (you provide this in real systems; Claude infers it in this exercise) |
| `finished` | boolean | True when Claude has enough to produce a final recommendation |
| `confidence` | HIGH/MEDIUM/LOW | Only meaningful when `finished=true` |
| `recommended_action` | string | The final remediation step (only when `finished=true`) |
| `escalate` | boolean | True if human review is required |

**Your task:** Open `agent.py`. Implement `run_agent()` — build the loop, feed the previous iteration's output back into the next user message as `History`, and break when `finished=true` or `max_iterations` is reached. Run `--mock` first to see the expected output shape.

```bash
python module3/agent.py --mock                         # shows expected output
ANTHROPIC_API_KEY=sk-... python module3/agent.py       # your live implementation
```

If you get stuck, study `hello_agent.py` for a reference loop, or read `solutions/solution.py` for the full implementation.

---

## Expected Final Output (when finished=true)

```json
{
  "thought": "Exit code 137 is SIGKILL — OOM killer. Memory limit 512Mi vs peak 1.2Gi.",
  "action": "Patch memory limit to 2Gi and monitor next pod start.",
  "observation": "Analysis complete.",
  "finished": true,
  "confidence": "HIGH",
  "recommended_action": "kubectl patch deployment checkout-api -p '{...}'",
  "escalate": false
}
```

Full result saved to `output/output_module3.json`.

---

## Sample Data

`sample_data.json` contains a K8s OOMKill event for `checkout-api`:
- Exit code 137 (SIGKILL)
- Memory requests: 512Mi, limit: 512Mi
- Peak usage before kill: 1.2Gi
- 8 restarts in 22 minutes

---

## What's happening under the hoods?

`finished=true` is the loop's exit condition — not `max_iterations`. The agent stops as soon as it has enough information, which may be after 1 iteration or 5. This is the key difference between a ReAct agent and a fixed-step pipeline: the agent decides when it is done. `max_iterations` is a safety ceiling, not the expected number of steps. An agent that always runs to `max_iterations` is not reasoning — it is just looping.

---

## Success Criteria

- ReAct loop runs at least 1 iteration and exits cleanly (no unhandled exceptions)
- Each iteration prints `thought`, `action`, and `observation`
- Final result has `finished=true`, `confidence`, and `recommended_action`
- Full output saved to `output/output_module3.json`
- If `escalate=true`, an escalation notice is printed
