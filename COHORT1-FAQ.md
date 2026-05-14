# Cohort 1 — Frequently Asked Questions

> Last updated: May 2026

---

## Module 1

### Q: Where do I find and run the exercise files (verify_setup.py, hello_claude.py, etc.)?

**Asked by:** Anju Bala

All exercise files live in the course GitHub repository. Here is how to get to them:

**Step 1 — Clone the course repo**

If you haven't already, clone (or fork and clone) the course repository to your local machine:

```bash
git clone https://github.com/platformengineering/agentic-ai-pe-course.git
cd agentic-ai-pe-course
```

**Step 2 — Navigate to the Module 1 folder**

Each module has its own folder. All the files you listed are inside `module1/`:

```
module1/
├── verify_setup.py       ← Run this first — pre-flight environment check
├── hello_claude.py       ← Primary exercise script — write your system prompt here
├── agent.py              ← Alternative entry point that saves output to file
├── sample_log.txt        ← Sample CI failure log (agent input)
├── agent-config.yml      ← Model and output schema configuration
└── solutions/
    └── solution.py       ← Reference implementation — read after your own attempt
```

**Step 3 — Run the pre-flight check first**

From the root of the repo, run:

```bash
python module1/verify_setup.py
```

This checks that your Python version, dependencies, and API key are all configured correctly. Fix any issues it flags before moving on to `hello_claude.py`.

**Step 4 — Set your API key (if using the Claude API)**

```bash
export ANTHROPIC_API_KEY=your_key_here
```

`hello_claude.py` supports two flags for running without making a live API call:

- `--manual` — prints the formatted prompt so you can paste it into Claude.ai for free. No API key needed.
- `--mock` — simulates a real API response locally. Useful for testing your code without consuming tokens.

```bash
python module1/hello_claude.py --manual   # paste prompt into Claude.ai manually
python module1/hello_claude.py --mock     # local mock response, no API call
```

---

*More questions will be added here as they come in. If you have a question, post it in the Slack course channel.*