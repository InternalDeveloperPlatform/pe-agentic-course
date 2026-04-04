# Module 3 Solution

## The ReAct Pattern
Each iteration: **Thought** → **Action** → **Observation** → (repeat until finished=true)

The agent uses its `thought` to decide which tool to call (`action`), executes the tool, and incorporates the `observation` into the next iteration.

## Key Learning: exit code 137 = OOMKill
- Exit code 137 = 128 + signal 9 (SIGKILL)  
- The kernel sends SIGKILL when a container exceeds its memory limit
- The fix is either `kubectl set resources` to increase the limit, or fixing the memory leak in the application

## Comparing CI vs K8s Scenarios
The same ReAct loop handles both. The only differences:
- Context JSON structure (pod fields vs CI fields)
- System prompt output schema (kubectl_fix_command vs code_fix_snippet)
- Tool definitions (describe_pod vs fetch_workflow_log)

This is the core architectural lesson: the loop is stable infrastructure, the schema is the variable.
