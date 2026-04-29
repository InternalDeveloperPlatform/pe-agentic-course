# docs/

Architecture diagrams, system prompt reference, and quick-reference guides for the course.

---

## architecture/

Mermaid flowchart diagrams for each module's agent architecture.
Render in VS Code (Mermaid Preview extension), GitHub (native), or any Mermaid viewer.

| File | What it shows |
|------|---------------|
| `module1.mermaid` | Single-shot hello_claude.py flow |
| `module2.mermaid` | Structured JSON triage agent |
| `module3.mermaid` | ReAct loop with history accumulation |
| `module4.mermaid` | CI/CD diagnostic agent with multi-source log input |
| `module5.mermaid` | Quality gate + post-deploy monitor (two agents) |
| `module6.mermaid` | Two-phase conversational observability agent |
| `module7.mermaid` | Parallel multi-agent orchestrator with conflict detection |
| `module8.mermaid` | Full 5-step capstone pipeline |

---

## prompts/

### `system-prompts.md`
Every system prompt used in the course, with the output JSON schema for each.
Use this as a copy-paste reference when building your own agents.

### `prompt-engineering-tips.md`
Ten practical prompt engineering lessons from building the course agents:
- Forcing JSON-only output
- Calibrating confidence levels
- Termination conditions for ReAct loops
- Routing vs. analysis prompt separation
- Token budget guidelines

---

## reference/

### `claude-api-quickref.md`
- The `ask()` function signature and all parameters
- Available Claude models and when to use each
- Token budget recommendations by agent type
- Error handling patterns
- Cost estimates

### `react-pattern.md`
- Single-shot vs. ReAct decision guide
- The iteration JSON schema
- Full Python implementation pattern
- Context growth across iterations
- Confidence calibration rules
- Debugging guide (common failure modes)
