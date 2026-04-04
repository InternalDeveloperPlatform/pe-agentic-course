# Module 4 Solution

## Key Learning: MEDIUM Confidence is Correct Here
The agent should output `confidence: MEDIUM` and `escalate: true` — not HIGH.

**Why not HIGH?**
- The CI pipeline passed — no code error
- The OOMKill is a runtime observation, not a deterministic code analysis  
- The "root cause" (memory limit too low) is an inference, not a fact proven by the log

**Why MEDIUM is honest:**
- We can see the memory usage is close to the limit (memory_headroom_pct will be low)
- But we don\'t know if this is a memory leak or a workload spike
- The safe action is to escalate for human review before changing resource limits

## Contrast with Module 2 Demo (HIGH Confidence)
The Module 2 demo showed a NameError — the log literally says `NameError: name "statis" is not defined`. That is deterministic. HIGH confidence is correct.

An OOMKill requires an inference. MEDIUM + escalate is more professional and safer.
