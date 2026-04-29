#!/bin/bash
# Module 2 — Agentic AI Fundamentals: How Agents Reason and Act
# Run from code-repo/: bash runners/module2.sh

BLUE='\033[0;34m'; CYAN='\033[0;36m'; GREEN='\033[0;32m'
YELLOW='\033[1;33m'; MAGENTA='\033[0;35m'; RED='\033[0;31m'
BOLD='\033[1m'; NC='\033[0m'

MOCK_MODE=false
[[ -z "$ANTHROPIC_API_KEY" ]] && MOCK_MODE=true

press_enter() {
  echo ""; echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
  echo -e "${YELLOW}  ↵  Press ENTER to continue...${NC}"
  echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"; read
}

section() {
  local width=70 len=${#1} pad=""
  (( len < width )) && printf -v pad "%$((width - len))s" ""
  echo ""; echo -e "${BLUE}╔════════════════════════════════════════════════════════════════════════╗${NC}"
  echo -e "${BLUE}║  ${1}${pad}║${NC}"
  echo -e "${BLUE}╚════════════════════════════════════════════════════════════════════════╝${NC}"; echo ""
}

cmd() { echo -e "  ${CYAN}\$ $1${NC}"; }
note() { echo -e "  ${GREEN}▶  $1${NC}"; }
warn() { echo -e "  ${RED}⚠  $1${NC}"; }

# ────────────────────────────────────────────────────────────────────────────────
section "Module 2 — Agentic AI Fundamentals: How Agents Reason and Act"
echo "Module 2 builds on Module 1 by introducing structured agent schemas."
echo "Instead of free-form text, agents return JSON — machines can act on it!"
echo ""

press_enter

# ────────────────────────────────────────────────────────────────────────────────
section "PREREQUISITES"
echo "Before running this module, ensure:"
echo ""

[[ -f "module1/sample_log.txt" ]] && note "✓ module1/sample_log.txt exists" || {
  warn "✗ module1/sample_log.txt not found"
  exit 1
}

[[ -f "shared/claude_client.py" ]] && note "✓ shared/claude_client.py exists" || {
  warn "✗ shared/claude_client.py not found"
  exit 1
}

if $MOCK_MODE; then
  note "Running in MOCK MODE (ANTHROPIC_API_KEY not set)"
else
  note "ANTHROPIC_API_KEY is set — live API calls enabled"
fi

echo ""
press_enter

# ────────────────────────────────────────────────────────────────────────────────
section "THE PROBLEM — A Real CI Failure Log"
echo "The agent will read this CI failure log and diagnose it:"
echo ""

cmd "cat module2/sample_log.txt"
cat module2/sample_log.txt
echo ""

note "This is what the agent sees — a text log snippet."
note "The agent must extract structure: summary, cause, and recommended fix."
echo ""

press_enter

# ────────────────────────────────────────────────────────────────────────────────
section "AGENT ARCHITECTURE — Defining the JSON Schema"
echo "The key to reliable agents: define EXACTLY what JSON you expect back."
echo ""

cmd "grep -A 5 'SYSTEM_PROMPT' module2/triage_agent.py"
grep -A 5 'SYSTEM_PROMPT' module2/triage_agent.py
echo ""

note "The SYSTEM_PROMPT defines the agent's role and output schema:"
note "  • Agent role: 'You are a CI/CD triage agent...'"
note "  • JSON keys: summary, likely_cause, next_step, confidence, escalate"
note "  • Constraint: confidence is HIGH only when root cause is directly visible"
note "  • Rule: escalate=true only if human intervention is needed"
echo ""

note "Without this schema, Claude might return:"
note "  • Free-form text (hard to parse)"
note "  • Different key names (inconsistent)"
note "  • Missing values (incomplete)"
note "  • Extra commentary (noisy)"
echo ""

press_enter

# ────────────────────────────────────────────────────────────────────────────────
section "MOCK RUN — See What the Agent Returns"
echo "Running triage_agent.py in mock mode (no API key required)..."
echo ""

cmd "python3 module2/triage_agent.py --mock"
python3 module2/triage_agent.py --mock
echo ""

note "The agent returned JSON with 5 keys:"
note "  • summary: brief description of the failure"
note "  • likely_cause: root cause explanation"
note "  • next_step: concrete remediation"
note "  • confidence: HIGH because the error is directly visible in the log"
note "  • escalate: false because the fix is self-contained"
echo ""

press_enter

# ────────────────────────────────────────────────────────────────────────────────
if ! $MOCK_MODE; then
  section "LIVE API RUN — Watch Claude Actually Reason"
  echo "Calling the real Claude API with your sample log..."
  echo ""

  cmd "python3 module2/triage_agent.py"
  python3 module2/triage_agent.py || {
    warn "API call failed. Check your API key and rate limits."
    exit 1
  }
  echo ""

  note "Compare the live output to the mock response above."
  note "Claude's reasoning may differ, but JSON structure is identical."
  echo ""

  press_enter
fi

# ────────────────────────────────────────────────────────────────────────────────
section "YOUR EXERCISE — Implement module2/agent.py"
echo ""
echo -e "${MAGENTA}┌──────────────────────────────────────────────────────────────┐${NC}"
echo -e "${MAGENTA}│ EXERCISE: Agent with Structured JSON Output                │${NC}"
echo -e "${MAGENTA}└──────────────────────────────────────────────────────────────┘${NC}"
echo ""

echo -e "${BOLD}What you'll implement:${NC}"
echo ""
echo "  1. Define SYSTEM_PROMPT in module2/agent.py"
echo "     • Instruct Claude it's a CI/CD triage agent"
echo "     • Specify JSON keys: summary, likely_cause, next_step, confidence, escalate"
echo "     • Add rule: confidence=HIGH only when root cause is visible in the log"
echo "     • Add rule: escalate=true only if human action is required"
echo ""
echo "  2. Implement run_agent() function:"
echo "     • Load the CI failure log: log = load_sample()"
echo "     • If MOCK_MODE: return MOCK_RESPONSE"
echo "     • Else: call ask(SYSTEM_PROMPT, f'CI failure log:\\n\\n{log}')"
echo "     • Return the result dict"
echo ""
echo "  3. Test with mock mode first:"
echo ""

echo -e "${CYAN}    $ python3 module2/agent.py --mock${NC}"
echo ""

echo -e "${BOLD}Then test with the real API:${NC}"
echo ""

echo -e "${CYAN}    $ python3 module2/agent.py${NC}"
echo ""

echo -e "${BOLD}Tips:${NC}"
note "The SYSTEM_PROMPT should be a multi-line string (use triple quotes)"
note "The 'confidence' rule is IMPORTANT — it prevents overconfident diagnoses"
note "The 'escalate' rule means 'does this need a human before applying the fix?'"
note "Use load_sample() to read module2/sample_log.txt"
echo ""

echo -e "${MAGENTA}Reference: module2/solutions/solution.py (peek if stuck)${NC}"
echo ""
