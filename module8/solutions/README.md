# Module 8 Capstone Solution

## The Full 5-Step Pipeline
1. **Detect** — classify the incoming event (CI_FAILURE, DEPLOY_COMPLETE, OOMKill, etc.)
2. **Diagnose** — run the Module 4 diagnostic agent on the event context
3. **Gate** — run the Module 5 quality gate to evaluate the proposed fix
4. **Remediate** — synthesise both outputs and decide: AUTO_FIX, ROLLBACK, or ESCALATE
5. **Notify** — create a GitHub Issue and write the Step Summary

## Every Module Is Here
- **M1** pattern: `ask()` + JSON parsing + `save_json()`
- **M2** pattern: five clearly separated functions
- **M3** pattern: multi-step reasoning (embedded in `step_diagnose`)
- **M4** pattern: context assembly from event payload
- **M5** pattern: gate evaluation before acting
- **M6** pattern: conversational output via `to_github_issue()`
- **M7** pattern: multi-agent synthesis in `step_remediate`

## Production Extension
To go from this solution to production:
1. Replace `sample_data.json` input with a real `workflow_run` event payload from GitHub
2. Uncomment the `gh issue create` subprocess call in `step_notify`
3. Add the `ANTHROPIC_API_KEY` and `GITHUB_TOKEN` secrets to your repository
4. Set the workflow trigger to `on: workflow_run: workflows: [CI] types: [completed]`
