# Module 1 Solution

## Key Concepts
- `ask()` wraps the Anthropic API. You pass a system prompt and user message; it returns parsed JSON.
- The system prompt defines the output schema. Claude produces exactly what the schema describes.
- The `save_json()` and `to_step_summary()` helpers are reused in every module.

## What Makes a Good System Prompt
1. **Role definition**: "You are a platform engineering assistant."
2. **Output instruction**: "Return ONLY valid JSON" — the word ONLY matters.
3. **Schema specification**: list every key with its type.
4. No open-ended instructions. No ambiguity.

## Running the Solution
```bash
python module1/solutions/solution.py
```

## Expected Output
```json
{
  "summary": "Deployment pipeline failed due to connection refused to internal registry",
  "likely_cause": "The container registry at registry.internal:5000 is unreachable",
  "next_step": "Verify registry.internal DNS resolution and network connectivity from the build runner"
}
```
