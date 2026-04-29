#!/bin/bash
# Module 4 — AI-Powered Diagnosis & Remediation
# Run from code-repo/: bash runners/module4.sh

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
section "Module 4 — AI-Powered Diagnosis & Remediation"
echo "Module 4 brings it all together: diagnose CI failures and suggest fixes."
echo "The agent reads stack traces and produces actionable remediation steps."
echo ""

press_enter

# ────────────────────────────────────────────────────────────────────────────────
section "PREREQUISITES"
echo "Module 3 should be complete. Verify these exist:"
echo ""

[[ -f "module3/agent.py" ]] && note "✓ module3/agent.py exists" || {
  warn "✗ module3/agent.py not found"
  exit 1
}

[[ -f "module4/broken_app/app.py" ]] && note "✓ module4/broken_app/app.py exists" || {
  warn "✗ module4/broken_app/app.py not found"
  exit 1
}

echo ""
press_enter

# ────────────────────────────────────────────────────────────────────────────────
section "THE BROKEN APP — Your CI Pipeline's Worst Enemy"
echo "This is the code that will trigger the CI pipeline failure:"
echo ""

cmd "cat module4/broken_app/app.py"
cat module4/broken_app/app.py
echo ""

note "This app has TWO bugs:"
note "  • Line 37: 'count += statis' — NameError (undefined variable)"
note "  • Line 44: 'version = app_version' — NameError (wrong constant name)"
note ""
note "These errors will crash your CI pipeline. The agent's job:"
note "  1. Parse the stack trace"
note "  2. Identify each NameError"
note "  3. Suggest the exact line-by-line fix"
echo ""

press_enter

# ────────────────────────────────────────────────────────────────────────────────
section "WATCH IT FAIL — See the Traceback"
echo "Running the broken app to capture the CI failure log:"
echo ""

cmd "python3 module4/broken_app/app.py 2>&1 || true"
python3 module4/broken_app/app.py 2>&1 || true
echo ""

note "This is EXACTLY what the CI pipeline captures when tests fail."
note "The agent will read this traceback and diagnose both bugs."
echo ""

press_enter

# ────────────────────────────────────────────────────────────────────────────────
section "DEMO: diagnose.py — The Diagnosis Agent"
echo "This is the reference implementation showing what your agent does:"
echo ""

cmd "python3 module4/diagnose.py --mock"
python3 module4/diagnose.py --mock
echo ""

note "The agent returned:"
note "  • error_type: 'NameError' (parsed from the traceback)"
note "  • root_cause: plain-English explanation of both bugs"
note "  • confidence: HIGH (NameErrors are deterministic, unambiguous)"
note "  • fix object: detailed line-by-line corrections"
note "    - file: exact path"
note "    - line: exact line number"
note "    - original: the buggy code"
note "    - corrected: the fixed code"
note "  • post_mortem: what happened, why, how to prevent"
note "  • escalate: false (fix is self-contained, no human approval needed)"
echo ""

press_enter

# ────────────────────────────────────────────────────────────────────────────────
if ! $MOCK_MODE; then
  section "DEMO LIVE: diagnose.py with Real Claude"
  echo "Calling the real Claude API to diagnose the broken app..."
  echo ""

  cmd "python3 module4/diagnose.py"
  python3 module4/diagnose.py || {
    warn "API call failed."
    exit 1
  }
  echo ""

  note "Compare live output to the mock response above."
  note "Claude's wording may differ, but JSON structure is identical."
  echo ""

  press_enter
fi

# ────────────────────────────────────────────────────────────────────────────────
section "PREVIEW: module4/triage_agent.py (Your Exercise)"
echo "This file currently has a NotImplementedError. Let's see it fail:"
echo ""

cmd "python3 module4/triage_agent.py --mock 2>&1 || true"
python3 module4/triage_agent.py --mock 2>&1 || true
echo ""

warn "This is intentional. The implementation is missing."
note "Your job is to fill in the run_agent() function."
echo ""

press_enter

# ────────────────────────────────────────────────────────────────────────────────
section "YOUR EXERCISE — Implement module4/triage_agent.py"
echo ""
echo -e "${MAGENTA}┌──────────────────────────────────────────────────────────────┐${NC}"
echo -e "${MAGENTA}│ EXERCISE: CI/CD Diagnostic Agent                            │${NC}"
echo -e "${MAGENTA}└──────────────────────────────────────────────────────────────┘${NC}"
echo ""

echo -e "${BOLD}What you'll implement:${NC}"
echo ""
echo "  1. Keep or refine SYSTEM_PROMPT in module4/triage_agent.py"
echo "     • Agent is a CI/CD pipeline triage agent"
echo "     • Receives failure log from GitHub Actions"
echo "     • Returns JSON with:"
echo "       - error_type: exception class (NameError, ImportError, etc.)"
echo "       - root_cause: one-paragraph plain-English explanation"
echo "       - confidence: HIGH for deterministic errors (NameError, SyntaxError)"
echo "       - fix: object with {file, line, original, corrected} for each bug"
echo "       - post_mortem: {what_happened, why_it_happened, how_to_prevent}"
echo "       - escalate: boolean (true if human approval needed)"
echo ""
echo "  2. Implement run_agent() function:"
echo "     • Load the sample context (incident data or broken_app traceback)"
echo "     • If MOCK_MODE: return MOCK_RESPONSE"
echo "     • Else: call ask(SYSTEM_PROMPT, context_message)"
echo "     • Return the result dict"
echo ""
echo "  3. The scenario is different from diagnose.py:"
echo "     • diagnose.py: reads an EXPLICIT stack trace (NameError visible)"
echo "     • triage_agent.py: reads SILENT FAILURES (service returns 503 no trace)"
echo "     • Confidence will be MEDIUM (inferred, not certain)"
echo ""
echo "  4. Test with mock mode first:"
echo ""

echo -e "${CYAN}    $ python3 module4/triage_agent.py --mock${NC}"
echo ""

echo -e "${BOLD}Then test with the real API:${NC}"
echo ""

echo -e "${CYAN}    $ python3 module4/triage_agent.py${NC}"
echo ""

echo -e "${BOLD}Important differences from diagnose.py:${NC}"
note "diagnose.py: receives an exception traceback → HIGH confidence"
note "triage_agent.py: receives silent 503 responses → MEDIUM confidence"
note "triage_agent.py: agent must infer what's wrong (no stack trace)"
note "triage_agent.py: fix suggestions are more tentative"
echo ""

echo -e "${BOLD}Tips:${NC}"
note "Look at module4/sample_data.json to see what silent failure looks like"
note "SYSTEM_PROMPT should guide Claude on distinguishing HIGH vs MEDIUM confidence"
note "fix object is required even when confidence is MEDIUM"
note "Reference: module4/solutions/solution.py (peek if stuck)"
echo ""

echo -e "${MAGENTA}Reference: module4/solutions/solution.py (peek if stuck)${NC}"
echo ""
