#!/bin/bash
# Module 1 — Platform Engineering Pain Points & the AI Opportunity
# Run from code-repo/: bash runners/module1.sh

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
section "Module 1 — Platform Engineering Pain Points & the AI Opportunity"
echo "Welcome to the Agentic AI for Platform Engineering course!"
echo ""
note "This interactive demo runner will walk you through each module."
note "You'll see real code, run live examples, and implement agent functions."
echo ""

press_enter

# ────────────────────────────────────────────────────────────────────────────────
section "DEPENDENCIES"
echo "Checking required Python packages and tools..."
echo ""

cmd "python3 --version"
python3 --version
echo ""

cmd "python3 -c \"import anthropic; print('anthropic', anthropic.__version__)\""
python3 -c "import anthropic; print('  ✓ anthropic', anthropic.__version__)" 2>/dev/null || {
  warn "anthropic not installed. Install with: pip install anthropic"
  exit 1
}
echo ""

note "Python 3 — runs all course exercises and the Claude API client"
note "anthropic package — handles authentication and API calls to Claude"
echo ""

if $MOCK_MODE; then
  warn "ANTHROPIC_API_KEY not set"
  note "Demo will run in MOCK MODE (no API calls, pre-defined responses)"
  note "To use the live API: export ANTHROPIC_API_KEY=sk-ant-..."
  echo ""
fi

press_enter

# ────────────────────────────────────────────────────────────────────────────────
section "ENVIRONMENT CHECK"
echo "Running module1/verify_setup.py to check everything is configured..."
echo ""

cmd "python3 module1/verify_setup.py"
python3 module1/verify_setup.py || {
  if $MOCK_MODE; then
    note "Setup check: API key is optional in MOCK MODE. Continuing..."
  else
    warn "Environment check failed. See output above."
    exit 1
  fi
}
echo ""

press_enter

# ────────────────────────────────────────────────────────────────────────────────
section "THE CODE — Claude API Wrapper"
echo "Every module uses the same ask() function from shared/claude_client.py."
echo "This is the ONLY file you don't touch — it wraps the Claude API into one call."
echo ""

cmd "head -40 shared/claude_client.py"
head -40 shared/claude_client.py
echo ""

note "This function:"
note "  • Loads your ANTHROPIC_API_KEY from the environment"
note "  • Sends system prompt + user message to Claude"
note "  • Parses the JSON response automatically"
note "  • Returns a Python dict ready to use"
echo ""

press_enter

# ────────────────────────────────────────────────────────────────────────────────
section "MOCK MODE DEMO"
echo "Running module1/hello_claude.py with --mock (no API key needed)..."
echo ""

cmd "python3 module1/hello_claude.py --mock"
python3 module1/hello_claude.py --mock
echo ""

note "This is what a successful agent response looks like:"
note "  • summary: one-line description of the failure"
note "  • likely_cause: root cause diagnosis"
note "  • next_step: concrete remediation action"
note "  • confidence: HIGH/MEDIUM/LOW in the diagnosis"
echo ""

press_enter

# ────────────────────────────────────────────────────────────────────────────────
if ! $MOCK_MODE; then
  section "LIVE API RUN"
  echo "Your ANTHROPIC_API_KEY is set. Calling the real Claude API..."
  echo ""

  cmd "python3 module1/hello_claude.py"
  python3 module1/hello_claude.py || {
    warn "API call failed. Check your API key and rate limits."
    exit 1
  }
  echo ""

  press_enter
fi

# ────────────────────────────────────────────────────────────────────────────────
section "OUTPUT FILE"
if [[ -f "output/output_module1.json" ]]; then
  echo "Module output saved to output/output_module1.json:"
  echo ""
  cmd "cat output/output_module1.json"
  cat output/output_module1.json
  echo ""
else
  note "No output file yet (created after running live exercises)"
fi

press_enter

# ────────────────────────────────────────────────────────────────────────────────
section "YOUR EXERCISE — Implement module1/agent.py"
echo ""
echo -e "${MAGENTA}┌──────────────────────────────────────────────────────────────┐${NC}"
echo -e "${MAGENTA}│ EXERCISE: AI-Powered CI Failure Diagnosis                    │${NC}"
echo -e "${MAGENTA}└──────────────────────────────────────────────────────────────┘${NC}"
echo ""

echo -e "${BOLD}What you'll do:${NC}"
echo "  1. Open module1/agent.py in your editor"
echo "  2. Define SYSTEM_PROMPT — instruct Claude to analyze a CI log and return JSON"
echo "     Keys: summary, likely_cause, next_step (all strings)"
echo "  3. Implement run_agent() function:"
echo "     • Load sample_log.txt"
echo "     • Call ask(SYSTEM_PROMPT, log_content)"
echo "     • Return the result dict"
echo "  4. Test with mock mode (no API key required):"
echo ""

echo -e "${CYAN}    $ python3 module1/agent.py --mock${NC}"
echo ""

echo -e "${BOLD}Then test with the real API:${NC}"
echo ""

echo -e "${CYAN}    $ export ANTHROPIC_API_KEY=sk-ant-...${NC}"
echo -e "${CYAN}    $ python3 module1/agent.py${NC}"
echo ""

note "Don't worry about perfect JSON schemas yet — Module 2 will formalize that."
note "For now, focus on making ask() work with a simple prompt."
echo ""

echo -e "${MAGENTA}Reference: module1/solutions/solution.py (peek if stuck)${NC}"
echo ""
