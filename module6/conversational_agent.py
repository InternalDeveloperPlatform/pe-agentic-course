"""
module6/conversational_agent.py
Conversational Observability Agent — Module 6 exercise script.

Takes a natural-language query about platform health, fetches live data from
the observability mock server (all four endpoints), and returns a structured
diagnostic response with a plain-English narrative.

This is the agent the student builds in the Module 6 exercise.
The reference implementation is in module6/solutions/solution.py.

Usage
-----
    # 1. Start the mock server in a separate terminal:
    python module6/observability_mock.py --scenario normal

    # 2. Run the agent (mock mode — no API key needed):
    python module6/conversational_agent.py --query "Is everything healthy?" --mock

    # 3. Run against all three scenarios:
    python module6/conversational_agent.py --query "Why is latency elevated?" --mock
    python module6/conversational_agent.py --query "We are getting paged. What's wrong?" --mock

    # 4. Run live against Claude:
    ANTHROPIC_API_KEY=sk-... python module6/conversational_agent.py --query "Is it safe to deploy?"

    # 5. Change the server scenario and re-query without restarting the agent:
    #    (Stop the mock server, restart with --scenario incident, then re-run the agent)

Two-phase design
----------------
Phase 1 — Routing: classify the query as health_check, investigation, or incident.
Phase 2 — Analysis: fetch the relevant endpoints and reason over the data.

This keeps individual Claude calls focused and token-efficient.

Output schema
-------------
{
  "query":            str,            # original natural-language query
  "query_type":       str,            # health_check | investigation | incident
  "status_summary":   str,            # one-sentence platform status
  "narrative":        str,            # human-readable diagnosis (2-4 sentences)
  "causal_chain":     list[str],      # ordered cause → effect chain (may be empty)
  "confidence":       str,            # HIGH | MEDIUM | LOW
  "recommended_action": str,          # concrete next step
  "deploy_safe":      bool | null,    # null if not applicable to the query
  "escalate":         bool,           # true if human should be paged
  "raw_platform_data": dict           # full snapshot from all four endpoints
}
"""

import os
import sys
import json
import argparse
import urllib.request
import urllib.error
from pathlib import Path
from datetime import datetime, timezone

sys.path.insert(0, str(Path(__file__).parent.parent))

from shared.claude_client import ask
from shared.output import save_json, to_step_summary, to_github_issue

# ── Configuration ──────────────────────────────────────────────────────────────

MOCK_MODE = "--mock" in sys.argv or os.environ.get("MOCK_MODE") == "1"
DEFAULT_SERVER = "http://localhost:8080"
MODEL = "claude-opus-4-5-20251101"
MAX_TOKENS = 1024

# ── Mock responses ─────────────────────────────────────────────────────────────
# Pre-baked responses for each of the three mock server scenarios.
# The agent detects which scenario is active from the fetched platform data
# and selects the matching mock response.

MOCK_RESPONSES = {
    "normal": {
        "query_type":         "health_check",
        "status_summary":     "All services healthy — platform operating within normal parameters.",
        "narrative":          (
            "All five services are reporting UP with latency well within baseline. "
            "Error rate is at 0.02% and no anomalies have been detected. "
            "The most recent deployment (user-service v2.3.1) completed successfully yesterday. "
            "Platform is in a stable state — safe to proceed with deployment."
        ),
        "causal_chain":       [],
        "confidence":         "HIGH",
        "recommended_action": "Proceed with deployment. No action required.",
        "deploy_safe":        True,
        "escalate":           False,
    },
    "high-load": {
        "query_type":         "investigation",
        "status_summary":     "Elevated latency on checkout-service driven by a 3.3x traffic spike.",
        "narrative":          (
            "A marketing campaign launched at 09:00 has driven traffic to 4,100 rps — 3.3x normal. "
            "Checkout-service is DEGRADED with P95 latency at 820ms versus a 180ms baseline. "
            "The DB connection pool is the likely bottleneck: more concurrent requests than pool slots. "
            "No code regression — this is a capacity issue. Consider horizontal scaling."
        ),
        "causal_chain":       [
            "Marketing campaign launched → 3.3x traffic spike",
            "checkout-service request queue depth exceeds DB connection pool capacity",
            "P95 latency increases 4.5x — requests queuing for DB connections",
        ],
        "confidence":         "HIGH",
        "recommended_action": "Scale checkout-service horizontally to at least 3 replicas. Monitor DB connection pool utilisation.",
        "deploy_safe":        False,
        "escalate":           False,
    },
    "incident": {
        "query_type":         "incident",
        "status_summary":     "ACTIVE INCIDENT — checkout-service DOWN due to OOMKill cascading to payment-service and api-gateway.",
        "narrative":          (
            "checkout-service v1.9.0 was deployed at 09:42 and introduced a 250k-record cache warm-up on startup. "
            "Memory peaked at 1.1Gi against a 512Mi limit, triggering an OOMKill at 09:43. "
            "The pod restart loop is causing 503s which have cascaded to payment-service (8.7% error rate) "
            "and tripped the api-gateway circuit breaker on /checkout/**. All checkout traffic is now blocked."
        ),
        "causal_chain":       [
            "deploy v1.9.0 introduced cache warm-up loading 250k records on startup",
            "startup memory spike: 1.1Gi peak vs 512Mi limit",
            "kernel OOM killer terminates checkout-service process (signal 9)",
            "pod enters restart loop → sustained 503s on /checkout/**",
            "payment-service dependency calls to checkout time out → error rate 0.1% → 8.7%",
            "api-gateway circuit breaker opens on /checkout/** → all checkout traffic blocked",
        ],
        "confidence":         "HIGH",
        "recommended_action": (
            "Immediate: roll back checkout-service to v1.8.x. "
            "Then: increase memory limit to 2Gi before re-deploying v1.9.0. "
            "Page the on-call engineer — P1 incident INC-20847 already open in PagerDuty."
        ),
        "deploy_safe":        False,
        "escalate":           True,
    },
}

# ── Phase 1 — Routing system prompt ────────────────────────────────────────────

ROUTING_SYSTEM_PROMPT = """\
You are a query classifier for a platform observability agent.
Classify the incoming query into exactly one of these types:
- health_check   : general status, deploy safety, "is everything OK?"
- investigation  : diagnosing elevated latency, error rates, or degraded (not down) services
- incident       : active outage, services DOWN, paging scenarios, "what is wrong right now?"

Return ONLY valid JSON with one key:
  { "query_type": "health_check" | "investigation" | "incident" }
"""

# ── Phase 2 — Analysis system prompt ───────────────────────────────────────────

ANALYSIS_SYSTEM_PROMPT = """\
You are a conversational platform observability agent. You receive:
1. A natural-language query from an engineer.
2. A snapshot of platform health data from four observability endpoints.

Analyse the data and answer the query concisely. Return ONLY valid JSON:
{
  "status_summary":     "<one sentence — current platform state>",
  "narrative":          "<2-4 sentences — plain English diagnosis or status, suitable for Slack>",
  "causal_chain":       ["<cause>", "<effect>", "..."],
  "confidence":         "HIGH | MEDIUM | LOW",
  "recommended_action": "<concrete next step — specific enough to act on immediately>",
  "deploy_safe":        true | false | null,
  "escalate":           true | false
}

Rules:
- causal_chain is an ordered list from root cause to visible symptom. Empty list [] if all services healthy.
- deploy_safe is true only if all services are UP and no anomalies exist. null if the query is not about deploying.
- escalate is true when a P1/P2 incident is active or when immediate human intervention is required.
- confidence is HIGH when root cause is unambiguous from the data, MEDIUM when inferred, LOW when data is insufficient.
- narrative must be readable by an engineer unfamiliar with the system — avoid internal jargon.
"""


# ── Data fetching ───────────────────────────────────────────────────────────────

def fetch_endpoint(base_url: str, path: str) -> dict:
    """Fetch a single observability endpoint. Returns the parsed JSON dict."""
    url = f"{base_url}{path}"
    try:
        with urllib.request.urlopen(url, timeout=5) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.URLError as exc:
        return {"error": str(exc), "endpoint": path}


def fetch_platform_data(base_url: str) -> dict:
    """Fetch all four observability endpoints and return a combined snapshot."""
    return {
        "health":    fetch_endpoint(base_url, "/health"),
        "metrics":   fetch_endpoint(base_url, "/metrics"),
        "anomalies": fetch_endpoint(base_url, "/anomalies"),
        "events":    fetch_endpoint(base_url, "/events"),
    }


def detect_mock_scenario(platform_data: dict) -> str:
    """Identify which mock scenario is active from the platform data snapshot."""
    anomaly_count = platform_data.get("anomalies", {}).get("count", 0)
    services = platform_data.get("health", {}).get("services", {})
    any_down = any(s.get("status") == "DOWN" for s in services.values())

    if any_down or anomaly_count >= 3:
        return "incident"
    if anomaly_count >= 1:
        return "high-load"
    return "normal"


# ── Agent phases ────────────────────────────────────────────────────────────────

def phase1_route(query: str) -> str:
    """Phase 1: classify the query type. Returns one of the three query type strings."""
    if MOCK_MODE:
        # Simple keyword-based routing for mock mode
        q = query.lower()
        if any(w in q for w in ["wrong", "down", "outage", "paged", "incident", "broken"]):
            return "incident"
        if any(w in q for w in ["slow", "latency", "elevated", "degraded", "scale"]):
            return "investigation"
        return "health_check"

    return ask(
        system=ROUTING_SYSTEM_PROMPT,
        user=f'Query: "{query}"',
        model=MODEL,
        max_tokens=64,
    ).get("query_type", "health_check")


def phase2_analyse(query: str, query_type: str, platform_data: dict) -> dict:
    """Phase 2: analyse platform data and produce the structured response."""
    if MOCK_MODE:
        scenario = detect_mock_scenario(platform_data)
        response = MOCK_RESPONSES[scenario].copy()
        return response

    user_msg = (
        f'Query: "{query}"\n'
        f'Query type: {query_type}\n\n'
        f'Platform data snapshot:\n{json.dumps(platform_data, indent=2)}'
    )
    return ask(
        system=ANALYSIS_SYSTEM_PROMPT,
        user=user_msg,
        model=MODEL,
        max_tokens=MAX_TOKENS,
    )


# ── Main ────────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Module 6 Conversational Observability Agent")
    parser.add_argument(
        "--query",
        required=True,
        help='Natural-language query, e.g. "Is it safe to deploy?" or "We are getting paged."',
    )
    parser.add_argument(
        "--server",
        default=DEFAULT_SERVER,
        help=f"Observability mock server base URL (default: {DEFAULT_SERVER})",
    )
    parser.add_argument(
        "--mock",
        action="store_true",
        help="Run in mock mode — no Claude API call, no live server required",
    )
    args = parser.parse_args()

    if args.mock and not MOCK_MODE:
        os.environ["MOCK_MODE"] = "1"

    print(f"[conversational_agent] Query   : {args.query}")
    print(f"[conversational_agent] Server  : {args.server}")
    print(f"[conversational_agent] Mock    : {MOCK_MODE}\n")

    # ── Fetch platform data ─────────────────────────────────────────────────────
    if MOCK_MODE:
        # In mock mode, pull scenario data directly from the mock server module.
        # Students can change scenario_key to "normal" or "high-load" to see different output.
        _mock_dir = str(Path(__file__).parent)
        if _mock_dir not in sys.path:
            sys.path.insert(0, _mock_dir)
        from observability_mock import SCENARIOS  # noqa: E402
        scenario_key = "incident"  # change to "normal" or "high-load" to see different output
        platform_data = SCENARIOS[scenario_key]
        print(f"[MOCK MODE] Using '{scenario_key}' scenario data (no server needed)")
        print(f"[MOCK MODE] In real mode, data is fetched live from {args.server}\n")
    else:
        print(f"[conversational_agent] Fetching platform data from {args.server}...")
        platform_data = fetch_platform_data(args.server)

        # Check for fetch errors
        errors = [k for k, v in platform_data.items() if "error" in v]
        if errors:
            print(f"⚠️  Could not reach endpoints: {errors}")
            print(f"   Is the mock server running?  python module6/observability_mock.py")
            sys.exit(1)

    print("[conversational_agent] Platform data fetched. Running two-phase analysis...\n")

    # ── Phase 1: Route ──────────────────────────────────────────────────────────
    query_type = phase1_route(args.query)
    print(f"[Phase 1 — Route] query_type: {query_type}")

    # ── Phase 2: Analyse ────────────────────────────────────────────────────────
    analysis = phase2_analyse(args.query, query_type, platform_data)

    # ── Assemble final result ───────────────────────────────────────────────────
    result = {
        "query":             args.query,
        "query_type":        query_type,
        "timestamp":         datetime.now(timezone.utc).isoformat(),
        **analysis,
        "raw_platform_data": platform_data,
    }

    print("\n── Response ──────────────────────────────────────────────────────────────")
    print(f"  Status    : {result.get('status_summary', '')}")
    print(f"  Narrative : {result.get('narrative', '')}")
    if result.get("causal_chain"):
        print("  Causal chain:")
        for step in result["causal_chain"]:
            print(f"    → {step}")
    print(f"  Confidence: {result.get('confidence', '')}")
    print(f"  Action    : {result.get('recommended_action', '')}")
    print(f"  Deploy OK : {result.get('deploy_safe')}")
    print(f"  Escalate  : {result.get('escalate')}")

    save_json(result, module=6)
    print(to_step_summary(result, title="Module 6 Conversational Agent Response"))

    if result.get("escalate"):
        print("\n🔴 ESCALATION REQUIRED — GitHub Issue body:")
        print(to_github_issue(result, module=6))

    return result


if __name__ == "__main__":
    main()
