# Module 5 Solution

## The Three Decisions
- **APPROVE**: all thresholds met, no conditions — safe to deploy now
- **APPROVE_WITH_CONDITIONS**: thresholds mostly met, known issues that must be tracked — deploy with follow-up
- **HOLD**: one or more blocking issues — do not deploy until resolved

## Why Thresholds Are Your Team\'s Risk Philosophy
The thresholds in the system prompt encode your team\'s risk tolerance. Changing `coverage_pct: minimum 80%` to `70%` is a policy decision, not a technical one. The agent enforces whatever you specify — it doesn\'t make risk judgements, it executes yours.

## Stretch Goal: The Sixth Dimension (Friday Deploy Risk)
The sixth gate dimension — Friday deploys with >500 lines changed → HIGH risk — demonstrates that agent gates can encode calendar and context awareness, not just metric thresholds.
