# Module 6 Solution

## The REPL Pattern
A simple read-eval-print loop: read a question, call the agent, print the answer, repeat.

The agent receives the full platform snapshot on every call — no session memory needed for basic queries. The `follow_up_questions` field guides the conversation naturally.

## The COST Intent (Stretch Goal)
To add a COST intent type:
1. Add `"COST"` to the intent enum in the system prompt
2. Add a condition in the REPL: if `result["intent"] == "COST"`, fetch `cost_per_request_delta` from the snapshot and format a cost trend response
3. The agent itself doesn\'t need to change — only the REPL logic that handles the intent

## Why This Scales
A dashboard requires an engineer to know which panel to look at. This agent requires only a question in plain English. Junior engineers with no Datadog training can query the full platform state immediately.
