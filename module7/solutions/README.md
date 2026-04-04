# Module 7 Solution

## Three-Stage Pipeline
1. **Orchestrate** — route the incident to the right specialists
2. **Investigate** — run specialists in parallel using `ThreadPoolExecutor`
3. **Synthesise** — detect conflicts and produce a unified decision

## Conflict Detection
Conflict is detected when `r1["recommended_action"] != r2["recommended_action"]`. The synthesis agent applies **Safety First**: when specialist recommendations conflict, the default is to escalate rather than auto-remediate.

## The Stretch Goal (Security Advisor)
Adding a third specialist requires:
1. A new entry in `SPECIALIST_PROMPTS` for `security_agent`
2. Updating the orchestrator system prompt to include `security_agent` in `available_specialists`
3. Updating the synthesis prompt to handle three-way conflicts
4. Running all three in parallel with `max_workers=3`

The orchestrator routing logic and synthesis logic do not change — only the configuration does.
