# Claude API Quick Reference

Everything you need to call the Claude API in this course.
All API calls go through `shared/claude_client.py` — you never call the SDK directly.

---

## The `ask()` function

```python
from shared.claude_client import ask

result = ask(
    system="Your system prompt here.",
    user="Your user message here.",
    model="claude-opus-4-5-20251101",   # optional, this is the default
    max_tokens=1024,                     # optional, default 1024
)
# result is always a Python dict (JSON parsed automatically)
```

### Parameters

| Parameter | Type | Default | Notes |
|-----------|------|---------|-------|
| `system` | `str` | required | System prompt — defines the agent's role and output schema |
| `user` | `str` | required | User message — the data to analyse |
| `model` | `str` | `claude-opus-4-5-20251101` | Claude model to use |
| `max_tokens` | `int` | `1024` | Max tokens in the response. Raise to 4096 for complex steps |

### Return value

Always returns a `dict`. Never returns raw text. If the API returns invalid JSON,
`ask()` raises a `ValueError` with the raw response text.

---

## Available Models

| Model string | Use when |
|---|---|
| `claude-opus-4-5-20251101` | All course exercises (default) |
| `claude-sonnet-4-5-20250929` | Faster, cheaper — good for routing/classification |
| `claude-haiku-4-5-20251001` | Very fast, cheapest — max_tokens=64 routing calls |

All three models are available in `shared/claude_client.py`. Change the model string
in the `AGENT_CONFIG` dict at the top of any module file.

---

## Token budgets by agent type

| Agent type | Typical max_tokens |
|---|---|
| Query classifier (Phase 1 route) | 64 |
| Single-shot triage (Module 2) | 512 |
| ReAct iteration (Module 3) | 1024 |
| Diagnostic agent with fix (Module 4) | 1024 |
| Gate / rollback agent (Modules 5, 7) | 1024 |
| Pipeline step with fix script (Module 8) | 4096 |

**Rule:** If you get a `json.loads()` error with "Unterminated string", raise `max_tokens`.
The response was cut off mid-JSON.

---

## Environment setup

```bash
# Set your API key (required for live calls)
export ANTHROPIC_API_KEY=sk-ant-...

# Verify the key works
python3 module1/verify_setup.py

# Every module supports mock mode (no key needed)
python3 moduleN/agent.py --mock
# or
MOCK_MODE=1 python3 moduleN/agent.py
```

---

## Cost estimates (approximate)

Based on claude-opus-4-5, as of course publication.
Actual costs depend on input context length — these are rough guides.

| Operation | Tokens (in+out) | Approx. cost |
|---|---|---|
| Single triage call | ~500 | ~$0.008 |
| ReAct loop (3 iterations) | ~2,000 | ~$0.030 |
| Module 8 full pipeline (5 steps) | ~5,000 | ~$0.075 |
| Module 6 routing call (Phase 1) | ~100 | ~$0.001 |

Prices from https://www.anthropic.com/pricing — check for current rates.

---

## Error handling

```python
from shared.claude_client import ask

try:
    result = ask(system=SYSTEM_PROMPT, user=user_message)
except ValueError as e:
    # JSON parse failed — raw response is in str(e)
    print(f"Parse error: {e}")
except Exception as e:
    # API error (rate limit, auth, network)
    print(f"API error: {e}")
```

Common errors:

| Error | Cause | Fix |
|---|---|---|
| `OSError: ANTHROPIC_API_KEY is not set` | Key not exported | `export ANTHROPIC_API_KEY=sk-ant-...` |
| `json.loads() ... Unterminated string` | Response truncated | Raise `max_tokens` |
| `AuthenticationError` | Key invalid or expired | Check key at console.anthropic.com |
| `RateLimitError` | Too many requests | Wait 60s, or upgrade tier |

---

## Model string reference

Always use the full model string with the date suffix:

```python
# Correct
model="claude-opus-4-5-20251101"
model="claude-sonnet-4-5-20250929"
model="claude-haiku-4-5-20251001"

# Wrong — will fail or use an unexpected model version
model="claude-opus"
model="claude-3-opus"
```
