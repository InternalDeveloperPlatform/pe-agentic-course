#!/bin/bash
# Module 3 — Environment Setup & Your First Agentic Workflow
# Run from code-repo/: bash runners/module3.sh

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
section "Module 3 — Environment Setup & Your First Agentic Workflow"
echo "Module 3 introduces ReAct (Reason + Act): agents that iterate and refine."
echo "Instead of one ask(), the agent loops: Thought → Action → Observation."
echo ""

press_enter

# ────────────────────────────────────────────────────────────────────────────────
section "PREREQUISITES"
echo "Module 2 should be complete. Verify these exist:"
echo ""

[[ -f "module2/triage_agent.py" ]] && note "✓ module2/triage_agent.py exists" || {
  warn "✗ module2/triage_agent.py not found"
  exit 1
}

[[ -f "module3/agent-config.yml" ]] && note "✓ module3/agent-config.yml exists" || {
  warn "✗ module3/agent-config.yml not found"
  exit 1
}

echo ""
press_enter

# ────────────────────────────────────────────────────────────────────────────────
section "CONFIG FILE — Agent Parameters"
echo "Each module has an agent-config.yml that defines runtime behavior:"
echo ""

cmd "cat module3/agent-config.yml"
cat module3/agent-config.yml
echo ""

note "max_iterations: 5 — the agent can loop up to 5 times before stopping"
note "model: claude-opus-4-5-20251101 — which Claude model to use"
note "max_tokens: 1024 — token limit per Claude API call"
echo ""

press_enter

# ────────────────────────────────────────────────────────────────────────────────
section "THE REACT PATTERN"
echo "ReAct (Reason + Act) is how agents solve multi-step problems:"
echo ""
echo -e "${BOLD}Iteration Flow:${NC}"
echo "  Iteration 1: Agent reasons about the problem → proposes one action"
echo "  Iteration 2: Agent observes the result → refines its thinking"
echo "  Iteration 3-N: Agent continues looping until finished=true"
echo ""

echo -e "${BOLD}Each iteration returns:${NC}"
echo "  • thought (string): agent's current reasoning"
echo "  • action (string): one specific investigation step"
echo "  • observation (string): what the agent would find if it did that action"
echo "  • finished (boolean): true when agent has a definitive conclusion"
echo "  • confidence (HIGH|MEDIUM|LOW): how sure the agent is"
echo "  • recommended_action (string): concrete fix (only when finished=true)"
echo "  • escalate (boolean): does a human need to approve before applying the fix?"
echo ""

note "The key insight: by forcing ONE action per iteration,"
note "we ensure the agent thinks step-by-step, not jumping to conclusions."
echo ""

press_enter

# ────────────────────────────────────────────────────────────────────────────────
section "INPUT DATA — An Incident to Diagnose"
echo "The agent will analyze this incident context:"
echo ""

cmd "cat module3/sample_data.json"
cat module3/sample_data.json
echo ""

note "This incident has:"
note "  • 23.4% error rate on payment-service"
note "  • P99 latency of 4820ms (should be <500ms)"
note "  • Recent deployments"
note "  • Logs showing DB connection pool exhaustion"
echo ""

note "Single-shot agent (Module 2): would guess 'DB pool too small'"
note "ReAct agent (Module 3): will iterate and consider:"
note "    Iteration 1: Check recent deploys (did code change trigger this?)"
note "    Iteration 2: Check DB load (is usage really high?)"
note "    Iteration 3: Estimate pool size needed (what's the fix?)"
echo ""

press_enter

# ────────────────────────────────────────────────────────────────────────────────
section "MOCK RUN — Watch the ReAct Loop"
echo "Running hello_agent.py in mock mode (single pre-computed iteration)..."
echo ""

cmd "python3 module3/hello_agent.py --mock"
python3 module3/hello_agent.py --mock
echo ""

note "The mock response shows ONE completed iteration:"
note "  • thought: agent's reasoning ('pod shows exit code 137 = SIGKILL = OOM')"
note "  • action: investigation step ('check memory requests/limits')"
note "  • observation: what the agent found ('peak 1.2Gi vs limit 512Mi')"
note "  • finished: true (agent is confident in the diagnosis)"
note "  • confidence: HIGH (exit code 137 is unambiguous)"
note "  • recommended_action: concrete fix ('kubectl patch to 2Gi limit')"
note "  • escalate: false (fix is self-contained)"
echo ""

press_enter

# ────────────────────────────────────────────────────────────────────────────────
if ! $MOCK_MODE; then
  section "LIVE API RUN — ReAct in Action"
  echo "Calling the real Claude API. Watch iterations accumulate..."
  echo ""

  cmd "python3 module3/hello_agent.py"
  python3 module3/hello_agent.py || {
    warn "API call failed."
    exit 1
  }
  echo ""

  note "Live runs may produce 2-5 iterations depending on the incident."
  note "Each iteration passes the full history to the next call."
  note "Claude uses prior reasoning to build on previous observations."
  echo ""

  press_enter
fi

# ────────────────────────────────────────────────────────────────────────────────
section "YOUR EXERCISE — Implement module3/agent.py"
echo ""
echo -e "${MAGENTA}┌──────────────────────────────────────────────────────────────┐${NC}"
echo -e "${MAGENTA}│ EXERCISE: ReAct Agent with Multi-Step Reasoning             │${NC}"
echo -e "${MAGENTA}└──────────────────────────────────────────────────────────────┘${NC}"
echo ""

echo -e "${BOLD}What you'll implement:${NC}"
echo ""
echo "  1. Define SYSTEM_PROMPT in module3/agent.py"
echo "     • Agent is a ReAct-pattern incident analysis agent"
echo "     • Each iteration: thought, action, observation, finished, confidence"
echo "     • finished=true only when agent has a definitive conclusion"
echo "     • Include recommended_action and escalate flags"
echo ""
echo "  2. Implement run_agent() function:"
echo "     • Initialize: history = []"
echo "     • Loop: for i in range(max_iterations):"
echo "       - Build user_msg:"
echo "         (iteration 0) user_msg = 'Incident context: ' + json.dumps(sample_data)"
echo "         (iteration 1+) user_msg += '\\n\\nPrior iterations:\\n' + json.dumps(history)"
echo "       - Call ask(SYSTEM_PROMPT, user_msg) → get result dict"
echo "       - Append result to history"
echo "       - If result['finished'] == true: break"
echo "     • Return the full history (list of all iterations)"
echo ""
echo "  3. Test with mock mode first:"
echo ""

echo -e "${CYAN}    $ python3 module3/agent.py --mock${NC}"
echo ""

echo -e "${BOLD}Then test with the real API (watch multiple iterations):${NC}"
echo ""

echo -e "${CYAN}    $ python3 module3/agent.py${NC}"
echo ""

echo -e "${BOLD}Tips:${NC}"
note "First iteration: NO prior history, just the incident context"
note "Next iterations: pass back all previous thought/action/observation"
note "Break the loop early if finished=true (don't waste API calls)"
note "max_iterations prevents infinite loops (default 5 in agent-config.yml)"
note "Each ask() call includes more context, so Claude can refine its reasoning"
echo ""

echo -e "${MAGENTA}Reference: module3/solutions/solution.py (peek if stuck)${NC}"
echo ""
