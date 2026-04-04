# Module 2 Solution

## The Five Steps
Each step is a separate function — this makes each responsibility explicit and testable:

1. **write_prompt** — assemble the system prompt and user message
2. **call_api** — invoke Claude via `ask()`
3. **parse_json** — validate all required keys are present
4. **execute_action** — act on the result (print, create Issue, etc.)
5. **verify_result** — confirm the result meets success criteria

## Why Separate Functions?
In production agents, each step can fail independently. Breaking them apart means:
- You can unit-test each step with a mock
- You can retry specific steps without re-running the full pipeline
- You can log the output of each step for debugging

## Key Learning
The stretch goal (adding a second scenario) reveals the agent architecture is scenario-agnostic. The five functions stay exactly the same — only the `sample_log.txt` content changes.
