# The ReAct Pattern — Reference Guide

ReAct (Reason + Act) is the iterative agent pattern introduced in Module 3.
This guide explains the pattern, when to use it, and how to implement it.

---

## What is ReAct?

ReAct is a loop: the agent alternates between reasoning about a problem and taking
one action, observing the result, then reasoning again.

```
Thought → Action → Observation → [repeat until finished]
```

Each iteration adds one step of understanding. The agent doesn't need to solve the
whole problem in one shot — it can investigate, discover, and refine.

---

## Single-shot vs. ReAct

| | Single-shot (Module 2) | ReAct (Module 3+) |
|--|--|--|
| API calls | 1 | 1–N (up to `max_iterations`) |
| Best for | Clear, unambiguous failures | Complex, multi-signal incidents |
| Output | One response dict | List of iteration dicts |
| Context per call | Static | Grows with each iteration |
| Cost | Fixed | Variable (but bounded by `max_iterations`) |

**Rule of thumb:** Use single-shot when the root cause is likely visible in the
input data. Use ReAct when investigation is required — when the agent needs to
form hypotheses and test them.

---

## The iteration schema

Each ReAct iteration returns this JSON structure:

```json
{
  "thought":            "My reasoning about the current state...",
  "action":             "One specific thing I will investigate next",
  "observation":        "What I find when I do that investigation",
  "finished":           false,
  "confidence":         "MEDIUM",
  "recommended_action": "",
  "escalate":           false
}
```

When `finished=true`, `recommended_action` contains the final diagnosis + fix:

```json
{
  "thought":            "I now have enough information...",
  "action":             "N/A — investigation complete",
  "observation":        "N/A",
  "finished":           true,
  "confidence":         "HIGH",
  "recommended_action": "kubectl patch deployment to set memory limit to 2Gi",
  "escalate":           false
}
```

---

## Implementation pattern

```python
def run_agent(incident_data: dict) -> list[dict]:
    history = []
    max_iterations = AGENT_CONFIG["max_iterations"]  # typically 5

    for i in range(max_iterations):
        # Build context — include history from iteration 1 onwards
        if i == 0:
            user_msg = f"Incident context:\n{json.dumps(incident_data, indent=2)}"
        else:
            user_msg = (
                f"Incident context:\n{json.dumps(incident_data, indent=2)}\n\n"
                f"Prior iterations:\n{json.dumps(history, indent=2)}"
            )

        result = ask(
            system=SYSTEM_PROMPT,
            user=user_msg,
            model=AGENT_CONFIG["model"],
            max_tokens=AGENT_CONFIG["max_tokens"],
        )

        history.append(result)

        if result.get("finished"):
            break

    return history
```

**Key points:**
- `history` is a list, not a dict. The final answer is `history[-1]`.
- Pass the full `history` back each iteration — not just the last one.
- Break on `finished=True` to avoid unnecessary API calls.
- `max_iterations` is a safety guard against infinite loops.

---

## Context growth across iterations

```
Iteration 1:  user_msg = incident_data (500 tokens)
Iteration 2:  user_msg = incident_data + iter_1 (700 tokens)
Iteration 3:  user_msg = incident_data + iter_1 + iter_2 (900 tokens)
Iteration 4:  user_msg = incident_data + iter_1 + iter_2 + iter_3 (1,100 tokens)
```

Context grows by roughly 200 tokens per iteration (one iteration dict).
For 5 iterations on a complex incident, budget ~1,500 input tokens total.
This is well within Claude's context window and has negligible cost impact.

---

## Confidence calibration in ReAct

| Confidence | When to use |
|---|---|
| `HIGH` | Root cause is deterministic — directly visible in the log or metrics (NameError, OOMKill with clear exit code, explicit connection timeout) |
| `MEDIUM` | Root cause is inferred from symptoms — multiple signals point the same direction but nothing is definitive (silent 503s, elevated latency without clear cause, flapping service) |
| `LOW` | Insufficient information — the agent has investigated but can't form a confident hypothesis |

**Important:** `HIGH` is only valid when `finished=true`. An agent should never
return `HIGH` confidence mid-investigation.

---

## When to escalate

Set `escalate=true` when:

- The fix requires changing production state (database migration, infrastructure config)
- Confidence is `MEDIUM` or `LOW` and the recommended action is destructive
- The incident affects a P1 service with revenue impact

Set `escalate=false` when:

- The fix is a code change with clear test coverage
- Confidence is `HIGH` and the fix is reversible
- The agent's recommended action is "monitor for 10 minutes"

---

## Debugging ReAct agents

**Agent hits `max_iterations` without `finished=true`:**
- System prompt missing explicit termination criteria
- Fix: add "Set `finished=true` once you can state a specific `recommended_action`."

**Agent returns `finished=true` on iteration 1 every time:**
- System prompt doesn't enforce single-action-per-iteration
- Fix: add "Take exactly one action per iteration. Do not jump to conclusions in iteration 1."

**Agent repeats the same action every iteration:**
- History not being passed back correctly
- Fix: verify your `user_msg` includes `json.dumps(history)` from iteration 1 onwards.

**Confidence is always `HIGH`:**
- Calibration rules missing from system prompt
- Fix: add explicit HIGH/MEDIUM/LOW definitions (see `prompts/system-prompts.md`).
