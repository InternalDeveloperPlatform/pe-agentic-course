# Prompt Engineering Tips for Agent Builders

Practical lessons from building the eight agents in this course.

---

## 1. Always specify the output format first

The single most impactful line in any agent system prompt:

```
Return ONLY valid JSON with these keys: ...
```

Without "ONLY", Claude adds explanation text before or after the JSON, which breaks `json.loads()`.
Without listing the keys, Claude invents its own key names, which breaks your schema checks.

---

## 2. Constrain enum fields explicitly

Bad:
```
- confidence: your assessment of how sure you are
```

Good:
```
- confidence (HIGH|MEDIUM|LOW): HIGH only when root cause is directly visible in the log
```

The enum constraint prevents drift (`"high"`, `"Very High"`, `"high confidence"`).
The calibration rule prevents overconfidence.

---

## 3. Define termination conditions for loop agents

ReAct agents need to know when to stop. Without an explicit rule, they loop forever.

```
- finished (boolean): true only when you have a definitive conclusion and can state
  a specific recommended_action. If you need more information, set finished=false.
```

And add a practical rule:
```
- Take exactly one action per iteration. Do not jump to conclusions in iteration 1.
```

---

## 4. Calibrate confidence — it's not just a label

`confidence` drives automation decisions downstream. An agent that returns `HIGH` on
everything is useless. Write explicit calibration rules:

```
- HIGH: root cause is directly visible in the log (NameError, SyntaxError, OOMKill with clear metrics)
- MEDIUM: cause is inferred from symptoms (silent 503s, flapping services, unknown error rates)
- LOW: insufficient information to form a hypothesis
```

---

## 5. Never use markdown in body-text fields

When an agent output will be embedded in JSON (e.g., `github_issue_body`), prohibit markdown:

```
- github_issue_body (string): 2-3 sentence plain-text summary
  (NO markdown, NO tables, NO code blocks, NO newlines)
```

Markdown inside a JSON string value causes `json.loads()` to fail if there are
literal newlines. Use a plain-text constraint or post-process with a sanitizer.

---

## 6. Separate routing from analysis

Two separate calls beat one complex call:

| | Phase 1: Route | Phase 2: Analyse |
|--|--|--|
| Tokens | 64 | 1024 |
| Cost | ~0.001¢ | ~0.01¢ |
| Prompt | Simple classifier | Full analytical prompt |
| Latency | ~200ms | ~1–2s |

Route first, analyse only when needed. This makes high-frequency health polling
affordable and keeps the analysis prompt focused.

---

## 7. Pass accumulated context in loops

Each ReAct iteration should receive the full prior history:

```python
# Iteration 0: just the incident
user_msg = f"Incident context:\n{json.dumps(incident_data)}"

# Iteration 1+: incident + all prior iterations
user_msg = (
    f"Incident context:\n{json.dumps(incident_data)}\n\n"
    f"Prior iterations:\n{json.dumps(history, indent=2)}"
)
```

Without prior history, each iteration starts from scratch. The agent can't build
on previous reasoning and will repeat the same first step every time.

---

## 8. Use `max_tokens` as a guard, not a budget

Set `max_tokens` high enough to never truncate a valid response:

- Simple classifiers: 64–128
- Single-shot triage agents: 512–1024
- Complex pipeline steps (FIX_OR_ESCALATE, REPORT): 2048–4096

Truncation mid-JSON causes `json.loads()` to fail. Budget by writing tighter
prompts (shorter required responses), not by lowering `max_tokens`.

---

## 9. Safety rules belong in the prompt, not only in code

The Rollback Agent prompt includes:
```
Safety rules: never recommend IMMEDIATE rollback if db_migration_present=true.
Only recommend rollback if deploy_age_minutes < 30 AND rollback_available=true.
```

These rules are also enforced in the orchestrator's `detect_conflict()` function.
Defense in depth: the prompt prevents bad LLM output; the code prevents bad
downstream action even if the prompt fails.

---

## 10. Test with mock before testing with the real API

Every agent in this course has a `--mock` flag that returns a pre-defined response.
Use it to:

1. Verify your output parsing code before spending API credits
2. Develop the downstream logic (GitHub Issue creation, Slack notification) without
   waiting for a live API call
3. Run CI tests deterministically without an API key

The mock response should represent the *expected* output shape, not a trivially
easy case. Use the borderline scenario: `APPROVE_WITH_CONDITIONS`, `MEDIUM` confidence,
`escalate: false`.
