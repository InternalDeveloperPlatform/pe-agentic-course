#!/bin/bash
# Module 5 — Intelligent CI/CD and Adaptive Delivery
# Run from code-repo/: bash runners/module5.sh

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

cmd() { echo -e "  ${CYAN}\$ $1${NC}"; echo ""; }
note() { echo -e "  ${GREEN}▶  $1${NC}"; }
warn() { echo -e "  ${RED}⚠  $1${NC}"; }

# ────────────────────────────────────────────────────────────────────────────────
section "Module 5 — Intelligent CI/CD and Adaptive Delivery"
echo "Welcome to Module 5! You'll build a pre-deploy quality gate agent that"
echo "evaluates release readiness and decides whether to APPROVE, HOLD, or"
echo "APPROVE_WITH_CONDITIONS. You'll also build a post-deploy monitor that"
echo "watches live metrics and recommends rollback."
echo ""

press_enter

# ────────────────────────────────────────────────────────────────────────────────
section "DEPENDENCIES"
echo "Module 5 builds on Module 4 (quality gate configuration)."
echo "The key configuration file defines six threshold dimensions:"
echo ""

cmd "cat module5/quality-gates.json"
cat module5/quality-gates.json
echo ""

note "These six gates are the decision boundaries:"
note "  • test_coverage (95%): strict — code quality baseline"
note "  • coverage_branch (80%): branch coverage threshold"
note "  • sast_findings (0): no high-severity security issues"
note "  • lighthouse_score (85): performance score minimum"
note "  • latency_p95_delta (10%): regression trigger (rollback-enabled)"
note "  • cost_per_request_delta (10%): spending regression warning"
echo ""
note "Students will edit these thresholds to trigger all three decisions."
echo ""

press_enter

# ────────────────────────────────────────────────────────────────────────────────
section "THE SCENARIO"
echo "Friday deploy window. Here's the pipeline snapshot:"
echo ""

cmd "head -20 module5/sample_data.json"
head -20 module5/sample_data.json
echo ""

note "Analysis:"
note "  • Coverage: 81.4% (below 95% threshold, but not regressed from previous)"
note "  • Test pass rate: 99.03% (excellent)"
note "  • SAST: 1 HIGH finding (critical issue!)"
note "  • Lighthouse: Not shown in sample, but included in gate evaluation"
echo ""
note "Classic APPROVE_WITH_CONDITIONS scenario: most gates pass, but coverage"
note "is below threshold and the Friday window adds risk. The triage agent must"
note "balance release readiness against deployment risk."
echo ""

press_enter

# ────────────────────────────────────────────────────────────────────────────────
section "PRE-DEPLOY GATE: MOCK MODE"
echo "The triage_agent.py evaluates release readiness. In mock mode, it returns"
echo "APPROVE_WITH_CONDITIONS with three conditions attached:"
echo ""

cmd "python3 module5/triage_agent.py --mock"
python3 module5/triage_agent.py --mock
echo ""

note "Notice the output shape:"
note "  • decision: APPROVE | APPROVE_WITH_CONDITIONS | HOLD"
note "  • conditions[]: list of constraints if decision != APPROVE"
note "  • risk_score: LOW | MEDIUM | HIGH"
note "  • escalate: true if human intervention needed"
echo ""

press_enter

# ────────────────────────────────────────────────────────────────────────────────
if $MOCK_MODE; then
  warn "SKIPPING live API call (ANTHROPIC_API_KEY not set)"
else
  section "PRE-DEPLOY GATE: LIVE API CALL"
  echo "Running the real triage_agent.py against Claude..."
  echo ""

  cmd "python3 module5/triage_agent.py"
  python3 module5/triage_agent.py
  echo ""

  press_enter
fi

# ────────────────────────────────────────────────────────────────────────────────
section "POST-DEPLOY MONITOR: MOCK MODE"
echo "The monitor.py runs AFTER deploy on a timed check, watching live metrics."
echo "It evaluates whether rollback is needed based on the quality-gates thresholds."
echo ""

cmd "python3 module5/monitor.py --mock"
python3 module5/monitor.py --mock
echo ""

note "Notice:"
note "  • rollback_recommended: true if metrics breach rollback thresholds"
note "  • severity: NONE | SCHEDULED | IMMEDIATE"
note "  • trigger: which gate caused the recommendation"
note "  • verification_steps[]: steps to verify rollback safety"
echo ""

press_enter

# ────────────────────────────────────────────────────────────────────────────────
if $MOCK_MODE; then
  warn "SKIPPING live API call (ANTHROPIC_API_KEY not set)"
else
  section "POST-DEPLOY MONITOR: LIVE API CALL"
  echo "Running the real monitor.py against Claude..."
  echo ""

  cmd "python3 module5/monitor.py"
  python3 module5/monitor.py
  echo ""

  press_enter
fi

# ────────────────────────────────────────────────────────────────────────────────
section "OUTPUT FILES"
echo "Both agents save their JSON output to the output/ directory for integration"
echo "with downstream systems (GitHub Issues, Slack, PagerDuty)."
echo ""

cmd "cat output/output_module5.json 2>/dev/null | head -30 || echo 'Run live to generate output'"
cat output/output_module5.json 2>/dev/null | head -30 || echo -e "  ${GREEN}▶  Run live to generate output${NC}"
echo ""

press_enter

# ────────────────────────────────────────────────────────────────────────────────
section "EXERCISE: Threshold Calibration"
echo "Your task: edit module5/quality-gates.json and trigger all three decisions."
echo ""
echo "Part 1: Force each decision"
echo "  1. APPROVE:              lower all thresholds to easy-to-meet values"
echo "  2. APPROVE_WITH_CONDITIONS: set a few to borderline values"
echo "  3. HOLD:                 set at least one to a blocking value"
echo ""
echo "For each state, run the triage_agent.py --mock and verify the decision changes."
echo ""
echo "Part 2: Trigger rollback recommendations"
echo "  1. Edit latency_p95_delta threshold from 10% down to 5%"
echo "  2. Run monitor.py --mock"
echo "  3. Verify rollback_recommended becomes true"
echo ""
echo "Remember: you are NOT writing code. You are calibrating thresholds"
echo "to match real deployment risk policies."
echo ""

press_enter

echo -e "${MAGENTA}╔══════════════════════════════════════════════════════════════╗${NC}"
printf "${MAGENTA}║  %-60s║${NC}\n" "START HERE: Edit quality-gates.json"
echo -e "${MAGENTA}╚══════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo "Edit the 'threshold' values in module5/quality-gates.json, then run:"
echo ""
echo -e "  ${CYAN}\$ python3 module5/triage_agent.py --mock${NC}"
echo -e "  ${CYAN}\$ python3 module5/monitor.py --mock${NC}"
echo ""
echo "After your edits, check the decision field in the output."
echo ""
