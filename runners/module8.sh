#!/bin/bash
# Module 8 — Build Your Platform Engineering Agent (Capstone)
# Run from code-repo/: bash runners/module8.sh

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
section "Module 8 — Build Your Platform Engineering Agent (Capstone)"
echo "Welcome to Module 8 — the capstone project! You'll build a production-grade"
echo "agent that integrates everything from Modules 1–7 into a single 5-step"
echo "pipeline that handles CI/CD failures end-to-end."
echo ""

press_enter

# ────────────────────────────────────────────────────────────────────────────────
section "DEPENDENCIES & ARCHITECTURE"
echo "Module 8 integrates all prior modules. The agent implements a 5-step pipeline:"
echo ""
echo "  Step 1  INGEST         Classify the CI/CD failure event"
echo "          ↓ output: event_type, service, failure_stage, severity"
echo ""
echo "  Step 2  DIAGNOSE       Root cause analysis using failure context"
echo "          ↓ output: error_type, root_cause, confidence, fix_possible"
echo ""
echo "  Step 3  GATE           Evaluate quality gates and release readiness"
echo "          ↓ output: decision, rationale, blocking_issues, risk_score"
echo ""
echo "  Step 4  FIX_OR_ESCALATE  Try auto-fix or escalate to humans"
echo "          ↓ output: path (AUTO_FIX|ESCALATE), reason, github_issue_*"
echo ""
echo "  Step 5  REPORT         Synthesize post-mortem and recommendations"
echo "          └─ output: post_mortem_summary, recommendations[]]"
echo ""
echo "Each step's output feeds the next step's context. This is the complete loop:"
echo "event → diagnosis → gate decision → action → post-mortem."
echo ""

press_enter

# ────────────────────────────────────────────────────────────────────────────────
section "THE PIPELINE IMPLEMENTATION PATTERN"
echo "Each step is implemented the same way. Here's the pattern:"
echo ""

cmd "grep -A 15 'def run_step_ingest' module8/platform_agent.py | head -20"
grep -A 15 'def run_step_ingest' module8/platform_agent.py | head -20
echo ""

note "Three lines per step:"
note "  1. Build context dict (event + prior steps)"
note "  2. Call ask() with step-specific system prompt"
note "  3. Parse response and return"
echo ""
note "Steps 2–5 are identical — different prompt, different context shape."
echo ""

press_enter

# ────────────────────────────────────────────────────────────────────────────────
section "FULL PIPELINE: MOCK MODE (PRE-BAKED RESPONSE)"
echo "Running the full pipeline with mock responses shows the expected output shape."
echo ""

cmd "python3 module8/platform_agent.py --simulate --mock"
python3 module8/platform_agent.py --simulate --mock
echo ""

note "Notice:"
note "  • Each step is executed in order"
note "  • Later steps have access to prior results"
note "  • Final output includes: recommended_action, github_issue_*, post_mortem_*"
note "  • The escalate flag triggers GitHub issue creation"
echo ""

press_enter

# ────────────────────────────────────────────────────────────────────────────────
section "WORKED EXAMPLE: THE INGEST STEP (DONE)"
echo "Module 8 provides the INGEST step as a fully-commented worked example."
echo "Read this carefully — it's the template for Steps 2–5."
echo ""

cmd "grep -B 5 -A 20 'def run_step_ingest' module8/platform_agent.py"
grep -B 5 -A 20 'def run_step_ingest' module8/platform_agent.py | head -30
echo ""

note "The pattern:"
note "  1. Build context: event_summary = {...}"
note "  2. Call ask(): response = ask(...)"
note "  3. Return: return response"
echo ""
note "That's it. Step 2 (DIAGNOSE) will be identical, except:"
note "  • Input context has event + ingest_result"
note "  • System prompt is DIAGNOSE_PROMPT instead of INGEST_PROMPT"
echo ""

press_enter

# ────────────────────────────────────────────────────────────────────────────────
if $MOCK_MODE; then
  warn "SKIPPING live API calls (ANTHROPIC_API_KEY not set)"
  warn "Live mode would:"
  warn "  1. Generate a synthetic CI failure event"
  warn "  2. Run all 5 steps against Claude"
  warn "  3. Save the full output to output/output_module8_platform_agent.json"
else
  section "LIVE RUN: FULL 5-STEP PIPELINE"
  echo "Running the real agent against Claude..."
  echo ""

  cmd "python3 module8/platform_agent.py --simulate"
  python3 module8/platform_agent.py --simulate
  echo ""

  press_enter
fi

# ────────────────────────────────────────────────────────────────────────────────
section "OUTPUT: FINAL REPORT"
echo "The agent saves its full output to output/output_module8_platform_agent.json."
echo ""

cmd "cat output/output_module8_platform_agent.json 2>/dev/null | python3 -m json.tool | head -50"
cat output/output_module8_platform_agent.json 2>/dev/null | python3 -m json.tool | head -50 || note "Run live to generate output"
echo ""

note "Key fields:"
note "  • steps.*: one entry per step (ingest, diagnose, gate, fix_or_escalate, report)"
note "  • final_output: recommended_action + escalate flag"
note "  • github_issue_*: ready to paste into a GitHub issue"
echo ""

press_enter

# ────────────────────────────────────────────────────────────────────────────────
section "EXERCISE: Implement the Four Missing Steps"
echo "Your task: complete four functions in module8/platform_agent.py"
echo ""
echo "Function 1: run_step_diagnose(event, ingest_result)"
echo "  • Input: event dict, output from INGEST step"
echo "  • Context: combine event + ingest_result into user message"
echo "  • Call ask() with DIAGNOSE_PROMPT"
echo "  • Return: diagnose_result dict"
echo ""
echo "Function 2: run_step_gate(event, diagnose_result)"
echo "  • Input: event dict, output from DIAGNOSE step"
echo "  • Context: combine event + diagnose_result"
echo "  • Call ask() with GATE_PROMPT"
echo "  • Return: gate_result dict"
echo ""
echo "Function 3: run_step_fix_or_escalate(event, diagnose, gate, pipeline_id)"
echo "  • Input: event, diagnose_result, gate_result, pipeline_id"
echo "  • Context: all three prior outputs"
echo "  • Call ask() with FIX_OR_ESCALATE_PROMPT"
echo "  • Parse response: if auto_fix_attempted=true, call save_fix_script()"
echo "  • Return: fix_or_escalate_result dict"
echo ""
echo "Function 4: generate_report(pipeline_id, steps_dict)"
echo "  • Input: pipeline_id, dict of all 4 completed steps"
echo "  • Context: all prior step outputs"
echo "  • Call ask() with REPORT_PROMPT"
echo "  • Return: report_result dict"
echo ""
echo "After implementing all 4 functions, test your work:"
echo ""

cmd "python3 module8/platform_agent.py --simulate --mock"
note "All 5 steps should execute without errors."
echo ""
note "Then run live to call Claude:"
echo ""

cmd "python3 module8/platform_agent.py --simulate"
note "Check that the final_output has recommended_action and escalate fields."
echo ""

press_enter

echo -e "${MAGENTA}╔══════════════════════════════════════════════════════════════╗${NC}"
printf "${MAGENTA}║  %-60s║${NC}\n" "START HERE: Implement DIAGNOSE, GATE, FIX_OR_ESCALATE, REPORT"
echo -e "${MAGENTA}╚══════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo "Read the worked example (run_step_ingest) carefully."
echo "Then copy the pattern for the four TODO functions."
echo ""
echo "Key points:"
echo "  • Use json.dumps(context_dict) to build the user message"
echo "  • Match the system prompt to the step (DIAGNOSE_PROMPT, etc)"
echo "  • Each function follows the 3-line pattern"
echo "  • Test after each one with --simulate --mock"
echo ""
echo "Pattern:"
echo ""
echo "  def run_step_diagnose(event, ingest_result):"
echo "      context = {"
echo "          'event': event,"
echo "          'ingest': ingest_result,"
echo "      }"
echo "      response = ask("
echo "          system=DIAGNOSE_PROMPT,"
echo "          user=json.dumps(context),"
echo "          model=MODEL,"
echo "          max_tokens=1024"
echo "      )"
echo "      return response"
echo ""
echo "Then implement GATE, FIX_OR_ESCALATE, and REPORT following the same pattern."
echo ""
