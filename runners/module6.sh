#!/bin/bash
# Module 6 — Operational Intelligence & Conversational Observability
# Run from code-repo/: bash runners/module6.sh

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
section "Module 6 — Operational Intelligence & Conversational Observability"
echo "Welcome to Module 6! You'll build a conversational observability agent that"
echo "answers natural-language questions about platform health by fetching live"
echo "metrics from a mock observability stack and reasoning over the data."
echo ""

press_enter

# ────────────────────────────────────────────────────────────────────────────────
section "DEPENDENCIES"
echo "Module 6 builds on Module 5. The key new component is a mock observability"
echo "server that simulates Datadog, Prometheus, and PagerDuty combined."
echo ""
echo "The observability_mock.py server provides four endpoints:"
echo ""

note "  /health       — per-service status (UP / DEGRADED / DOWN)"
note "  /metrics      — error rates, latency, throughput, memory usage"
note "  /anomalies    — detected anomalies with severity and correlation chains"
note "  /events       — recent deployments and config changes"
echo ""
echo "Three realistic scenarios built in:"
echo ""

note "  normal        All services healthy. Safe to deploy."
note "  high-load     Marketing campaign drove 3.3x traffic spike."
note "  incident      OOMKill in checkout-service, cascading failures."
echo ""

press_enter

# ────────────────────────────────────────────────────────────────────────────────
section "THE MOCK SERVER"
echo "Let's look at the scenario definitions:"
echo ""

cmd "grep -A 15 'SCENARIOS = {' module6/observability_mock.py | head -25"
grep -A 15 'SCENARIOS = {' module6/observability_mock.py | head -25
echo ""

note "The server switches scenarios with the --scenario flag."
note "The --mock flag in conversational_agent.py uses hardcoded mock responses"
note "keyed to the scenario data fetched from the mock server."
echo ""

press_enter

# ────────────────────────────────────────────────────────────────────────────────
section "SIMPLE AGENT: MOCK MODE"
echo "First, the simple single-shot agent. Fetch all platform data, send to Claude,"
echo "get back structured diagnosis in one call."
echo ""

cmd "python3 module6/agent.py --mock"
python3 module6/agent.py --mock
echo ""

note "Notice:"
note "  • answer: plain English, 1-3 sentences"
note "  • causal_chain: ordered list of root cause steps"
note "  • escalate: true if human should be paged"
echo ""

press_enter

# ────────────────────────────────────────────────────────────────────────────────
section "TWO-PHASE AGENT: NORMAL SCENARIO"
echo "The conversational_agent.py is more sophisticated. It has two phases:"
echo ""
echo "  Phase 1 — Routing:  classify the query as health_check/investigation/incident"
echo "  Phase 2 — Analysis: fetch data, reason over it, return structured response"
echo ""
echo "Running the normal scenario (no anomalies, safe to deploy):"
echo ""

cmd "python3 module6/conversational_agent.py --query \"Is everything healthy?\" --mock"
python3 module6/conversational_agent.py --query "Is everything healthy?" --mock
echo ""

note "The agent:"
note "  • Routed the query as query_type=health_check"
note "  • Fetched all four endpoints"
note "  • Detected: all services UP, zero anomalies, deploy_safe=true"
echo ""

press_enter

# ────────────────────────────────────────────────────────────────────────────────
section "TWO-PHASE AGENT: INCIDENT SCENARIO"
echo "Now an incident query (on-call engineer is paged):"
echo ""

cmd "python3 module6/conversational_agent.py --query \"We are getting paged. What is causing the latency spike?\" --mock"
python3 module6/conversational_agent.py --query "We are getting paged. What is causing the latency spike?" --mock
echo ""

note "The agent:"
note "  • Routed the query as query_type=incident"
note "  • Built a causal_chain with 6+ steps"
note "  • Detected escalate=true (human intervention needed)"
note "  • Provided recommended_action (rollback / scale / investigate)"
echo ""

press_enter

# ────────────────────────────────────────────────────────────────────────────────
if $MOCK_MODE; then
  warn "SKIPPING live API calls (ANTHROPIC_API_KEY not set)"
  warn "Live mode would:"
  warn "  1. Start the mock server as a background process"
  warn "  2. Run the agent against all three scenarios"
  warn "  3. Kill the server on EXIT"
else
  section "LIVE RUN: ALL SCENARIOS"
  echo "Starting the mock server in the background and running all three scenarios..."
  echo ""

  note "Scenario 1: normal"
  cmd "python3 module6/observability_mock.py --scenario normal"
  python3 module6/observability_mock.py --scenario normal > /dev/null 2>&1 &
  SERVER_PID=$!
  sleep 2

  cmd "python3 module6/conversational_agent.py --query \"Is it safe to deploy?\""
  python3 module6/conversational_agent.py --query "Is it safe to deploy?"
  echo ""

  kill $SERVER_PID 2>/dev/null
  sleep 1

  note "Scenario 2: incident"
  cmd "python3 module6/observability_mock.py --scenario incident"
  python3 module6/observability_mock.py --scenario incident > /dev/null 2>&1 &
  SERVER_PID=$!
  sleep 2

  cmd "python3 module6/conversational_agent.py --query \"We are getting paged. What is causing the latency spike?\""
  python3 module6/conversational_agent.py --query "We are getting paged. What is causing the latency spike?"
  echo ""

  kill $SERVER_PID 2>/dev/null

  press_enter
fi

# ────────────────────────────────────────────────────────────────────────────────
section "EXERCISE: Implement the Two-Phase Pipeline"
echo "Your task: complete the two missing functions in module6/conversational_agent.py"
echo ""
echo "Function 1: phase1_route()"
echo "  • Input: user query (string)"
echo "  • Call ask() with ROUTING_SYSTEM_PROMPT"
echo "  • Parse response: extract query_type field"
echo "  • Return: query_type (health_check | investigation | incident)"
echo ""
echo "Function 2: phase2_analyse()"
echo "  • Input: query, query_type, platform_data (JSON dict from all 4 endpoints)"
echo "  • Build context: combine query + query_type + platform_data into user message"
echo "  • Call ask() with ANALYSIS_SYSTEM_PROMPT"
echo "  • Parse response: extract all fields (narrative, causal_chain, escalate, etc)"
echo "  • Return: full response dict"
echo ""
echo "After implementing, verify your work:"
echo ""

cmd "python3 module6/conversational_agent.py --query \"Is everything healthy?\" --mock"
note "Check the output has query_type=health_check and deploy_safe=true"
echo ""

echo "Then test with the incident query:"
echo ""

cmd "python3 module6/conversational_agent.py --query \"We are getting paged. What is causing the latency spike?\" --mock"
note "Check query_type=incident and escalate=true"
echo ""

press_enter

echo -e "${MAGENTA}╔══════════════════════════════════════════════════════════════╗${NC}"
printf "${MAGENTA}║  %-60s║${NC}\n" "START HERE: Implement phase1_route() and phase2_analyse()"
echo -e "${MAGENTA}╚══════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo "Look at the stub functions in module6/conversational_agent.py."
echo "Each is 3-5 lines: call ask(), parse response, return result."
echo ""
echo "Starter pattern:"
echo ""
echo "  def phase1_route(query):"
echo "      response = ask("
echo "          system=ROUTING_SYSTEM_PROMPT,"
echo "          user=query,"
echo "          model=MODEL,"
echo "          max_tokens=64"
echo "      )"
echo "      return response.get('query_type')"
echo ""
echo "Test after each function:"
echo ""
echo -e "  ${CYAN}\$ python3 module6/conversational_agent.py --query ... --mock${NC}"
echo ""
