#!/bin/bash
# Module 7 — Multi-Agent Coordination & Implementation Strategy
# Run from code-repo/: bash runners/module7.sh

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
section "Module 7 — Multi-Agent Coordination & Implementation Strategy"
echo "Welcome to Module 7! You'll build an orchestrator that coordinates two"
echo "specialist agents running in parallel: a Gate Agent (pre-deploy) and a"
echo "Rollback Agent (post-deploy). The orchestrator detects conflicts and"
echo "applies conflict resolution strategies."
echo ""

press_enter

# ────────────────────────────────────────────────────────────────────────────────
section "DEPENDENCIES"
echo "Module 7 combines Modules 5 and 6. The orchestrator runs two agents:"
echo ""
echo "  1. Gate Agent (from Module 5)"
echo "     → Input: pipeline data, test results, coverage, security scan"
echo "     → Output: APPROVE / APPROVE_WITH_CONDITIONS / HOLD"
echo ""
echo "  2. Rollback Agent (from Module 5)"
echo "     → Input: live metrics, deployment age, risk thresholds"
echo "     → Output: rollback_recommended (true/false), severity, trigger reason"
echo ""
echo "The orchestrator runs both in parallel threads, collects results,"
echo "detects conflicts, and synthesizes a final recommendation."
echo ""

press_enter

# ────────────────────────────────────────────────────────────────────────────────
section "THE THREE CONFLICT SCENARIOS"
echo "Let's look at the three scenarios that demonstrate conflict detection:"
echo ""

cmd "grep -B 2 -A 8 'no_conflict\\|partial_conflict\\|full_conflict' module7/orchestrator.py | head -40"
grep -B 2 -A 8 'no_conflict.*:' module7/orchestrator.py | head -40
echo ""

note "Scenario definitions:"
note "  • no_conflict: Gate APPROVE + Rollback not recommended → SYNTHESISE (safe)"
note "  • partial_conflict: Gate APPROVE_WITH_CONDITIONS + Rollback SCHEDULED → SOFT_ESCALATE"
note "  • full_conflict: Gate APPROVE + Rollback IMMEDIATE → SAFETY_FIRST_ESCALATE"
echo ""
note "Key insight: When Rollback recommends IMMEDIATE but Gate approved, we apply"
note "Safety First policy — the incident responder always wins."
echo ""

press_enter

# ────────────────────────────────────────────────────────────────────────────────
section "SCENARIO 1: NO CONFLICT (Safe to Deploy)"
echo "Both agents agree: deploy is safe and no rollback needed."
echo ""

cmd "python3 module7/orchestrator.py --mock --scenario no_conflict"
python3 module7/orchestrator.py --mock --scenario no_conflict
echo ""

note "Notice:"
note "  • conflict.detected = false"
note "  • conflict.resolution = SYNTHESISE"
note "  • Final recommendation: DEPLOY"
echo ""

press_enter

# ────────────────────────────────────────────────────────────────────────────────
section "SCENARIO 2: PARTIAL CONFLICT (Soft Escalation)"
echo "Gate says APPROVE_WITH_CONDITIONS but Rollback recommends a SCHEDULED rollback."
echo "This is a soft conflict: conditions exist, but no immediate danger."
echo ""

cmd "python3 module7/orchestrator.py --mock --scenario partial_conflict"
python3 module7/orchestrator.py --mock --scenario partial_conflict
echo ""

note "Notice:"
note "  • conflict.detected = true"
note "  • conflict.type = SOFT_CONFLICT"
note "  • conflict.resolution = SOFT_ESCALATE"
note "  • Action: Inform on-call but don't block deployment"
echo ""

press_enter

# ────────────────────────────────────────────────────────────────────────────────
section "SCENARIO 3: FULL CONFLICT (Hard Escalation)"
echo "Gate approved but Rollback recommends IMMEDIATE rollback. This is dangerous:"
echo "the gate let a bad deploy through, and production is failing NOW."
echo ""
echo "Safety First policy: Incident Responder always wins."
echo ""

cmd "python3 module7/orchestrator.py --mock --scenario full_conflict"
python3 module7/orchestrator.py --mock --scenario full_conflict
echo ""

note "Notice:"
note "  • conflict.detected = true"
note "  • conflict.type = HARD_CONFLICT"
note "  • conflict.resolution = SAFETY_FIRST_ESCALATE"
note "  • Action: Page on-call, hold all deploys, consider rollback"
echo ""

press_enter

# ────────────────────────────────────────────────────────────────────────────────
section "CONVERT TO SLACK-READY MEMO"
echo "The interpret.py script takes the orchestrator JSON and converts it to"
echo "a plain-English escalation memo suitable for Slack or GitHub Issue."
echo ""

cmd "python3 module7/interpret.py --mock"
python3 module7/interpret.py --mock
echo ""

note "Notice the output:"
note "  • recommended_action: ESCALATE"
note "  • prioritised_tasks[]: ordered list for on-call"
note "  • rollout_memo: one paragraph for Slack"
echo ""

press_enter

# ────────────────────────────────────────────────────────────────────────────────
if $MOCK_MODE; then
  warn "SKIPPING live API calls (ANTHROPIC_API_KEY not set)"
  warn "Live mode would:"
  warn "  1. Start gate_agent and rollback_agent in parallel threads"
  warn "  2. Wait for both to complete"
  warn "  3. Detect conflict and synthesize final output"
else
  section "LIVE RUN: PARALLEL AGENTS"
  echo "Running the full scenario with real Claude API calls..."
  echo ""

  cmd "python3 module7/orchestrator.py --scenario full_conflict"
  python3 module7/orchestrator.py --scenario full_conflict
  echo ""

  press_enter
fi

# ────────────────────────────────────────────────────────────────────────────────
section "EXERCISE: Implement the Orchestrator"
echo "Your task: complete three functions in module7/orchestrator.py"
echo ""
echo "Function 1: run_gate_agent(pipeline_data)"
echo "  • Input: pipeline data (test results, coverage, security scan)"
echo "  • Call ask() with GATE_SYSTEM_PROMPT"
echo "  • Return: gate_result dict with decision, rationale, escalate, etc"
echo ""
echo "Function 2: run_rollback_agent(metrics_data)"
echo "  • Input: live metrics (error rate, latency, deployment age)"
echo "  • Call ask() with ROLLBACK_SYSTEM_PROMPT"
echo "  • Return: rollback_result dict with recommended, severity, trigger"
echo ""
echo "Function 3: detect_conflict(gate_result, rollback_result)"
echo "  • Input: outputs from both agents"
echo "  • Logic:"
echo "    - APPROVE + IMMEDIATE = HARD_CONFLICT (Safety First)"
echo "    - APPROVE_WITH_CONDITIONS + SCHEDULED = SOFT_CONFLICT"
echo "    - Otherwise = SYNTHESISE (no conflict)"
echo "  • Return: conflict dict with detected, type, resolution"
echo ""
echo "The main() function orchestrates:"
echo "  1. Start both agents in parallel with ThreadPoolExecutor"
echo "  2. Wait for both to complete"
echo "  3. Call detect_conflict() on results"
echo "  4. Return combined orchestrator_result"
echo ""
echo "Test after implementing:"
echo ""

cmd "python3 module7/orchestrator.py --mock --scenario no_conflict"
note "Check: conflict.detected = false, resolution = SYNTHESISE"
echo ""

cmd "python3 module7/orchestrator.py --mock --scenario full_conflict"
note "Check: conflict.detected = true, type = HARD_CONFLICT"
echo ""

press_enter

echo -e "${MAGENTA}╔══════════════════════════════════════════════════════════════╗${NC}"
printf "${MAGENTA}║  %-60s║${NC}\n" "START HERE: Implement the three orchestrator functions"
echo -e "${MAGENTA}╚══════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo "Pattern for run_gate_agent():"
echo ""
echo "  def run_gate_agent(pipeline_data):"
echo "      response = ask("
echo "          system=GATE_SYSTEM_PROMPT,"
echo "          user=json.dumps(pipeline_data),"
echo "          model=MODEL,"
echo "          max_tokens=1024"
echo "      )"
echo "      return response"
echo ""
echo "Pattern for detect_conflict():"
echo ""
echo "  def detect_conflict(gate, rollback):"
echo "      if gate['decision'] == 'APPROVE' and rollback['severity'] == 'IMMEDIATE':"
echo "          return {'detected': True, 'type': 'HARD_CONFLICT', 'resolution': 'SAFETY_FIRST_ESCALATE'}"
echo "      # ... other cases"
echo ""
echo "Test each scenario:"
echo ""
echo -e "  ${CYAN}\$ python3 module7/orchestrator.py --mock --scenario <name>${NC}"
echo ""
