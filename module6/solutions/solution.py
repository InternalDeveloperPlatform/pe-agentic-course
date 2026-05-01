"""
module6/solutions/solution.py
Reference solution for Module 6: Two-Phase Conversational Observability Agent.

What this module teaches
------------------------
The two-phase pattern separates a query into a cheap ROUTING step and a focused
ANALYSIS step:

  Phase 1 — Route  (max_tokens=64)
      Classify the incoming query: health_check | investigation | incident.
      Only 64 tokens needed — this is a classification task, not generation.

  Phase 2 — Analyse  (max_tokens=1024)
      Fetch live data from the relevant observability endpoints and produce
      the full structured diagnosis.

Why route first?
Without routing, you would pass ALL four endpoint payloads to Claude for every
query. A health_check query ("Is it safe to deploy?") doesn't need anomaly data;
an incident query doesn't need cost metrics. Routing first keeps each Claude call
focused on only the data that's actually relevant, reducing token cost and
improving reasoning quality.

The pattern scales: adding a new query type means adding a new route constant
and a new data-fetch strategy — not rewriting the agent.

What you implemented in the exercise
-------------------------------------
The two key functions in conversational_agent.py:

    def phase1_route(query: str) -> str:
        # Call ask() with ROUTING_SYSTEM_PROMPT (max_tokens=64)
        # Return result.get("query_type", "health_check")

    def phase2_analyse(query: str, query_type: str, platform_data: dict) -> dict:
        # Build user_msg combining query, query_type, and platform_data snapshot
        # Call ask() with ANALYSIS_SYSTEM_PROMPT (max_tokens=1024)
        # Return the result dict

This file shows both implementations with inline comments explaining each
design decision, plus a runnable main() that demos the full two-phase pipeline.

Compare with: module6/conversational_agent.py (the full exercise file)

Run
---
    python module6/solutions/solution.py --query "Is everything healthy?" --mock
    python module6/solutions/solution.py --query "We are getting paged. What's wrong?" --mock
    ANTHROPIC_API_KEY=sk-... python module6/solutions/solution.py --query "Is it safe to deploy?" --server http://localhost:8080
"""

import os
import sys
import json
import argparse
import urllib.request
import urllib.error
from pathlib import Path
from datetime import datetime, timezone

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from shared.claude_client import ask
from shared.output import save_json, to_step_summary, to_github_issue

# ── Mock mode ──────────────────────────────────────────────────────────────────
MOCK_MODE = "--mock" in sys.argv or os.environ.get("MOCK_MODE") == "1"

DEFAULT_SERVER = "http://localhost:8080"
MODEL          = "claude-opus-4-5-20251101"

# ── Mock responses — one per scenario ─────────────────────────────────────────
# Each scenario maps to what the agent produces when the mock server is serving
# that scenario's data. In real mode the agent generates these from live data.
MOCK_RESPONSES = {
    "normal": {
        "query_type":         "health_check",
        "status_summary":     "All services healthy — platform operating within normal parameters.",
        "narrative":          (
            "All five services are reporting UP with latency well within baseline. "
            "Error rate is at 0.02% and no anomalies have been detected. "
            "The most recent deployment completed successfully. "
            "Platform is in a stable state — safe to proceed with deployment."
        ),
        "causal_chain":       [],
        "confidence":         "HIGH",
        "recommended_action": "No action required. Proceed with deployment.",
        "deploy_safe":        True,
        "escalate":           False,
    },
    "high-load": {
        "query_type":         "investigation",
        "status_summary":     "Elevated latency on checkout-service driven by a 3.3x traffic spike.",
        "narrative":          (
            "A marketing campaign has driven traffic to 4,100 rps — 3.3x normal load. "
            "Checkout-service is DEGRADED with P95 latency at 820ms versus a 180ms baseline. "
            "The DB connection pool is the likely bottleneck — more concurrent requests than pool slots. "
            "No code regression. This is a capacity issue; consider horizontal scaling."
        ),
        "causal_chain":       [
            "Marketing campaign → 3.3x traffic spike to 4,100 rps",
            "checkout-service request queue exceeds DB connection pool capacity",
            "P95 latency increases 4.5x — requests queuing for DB connections",
        ],
        "confidence":         "HIGH",
        "recommended_action": "Scale checkout-service to at least 3 replicas. Monitor DB pool utilisation.",
        "deploy_safe":        False,
        "escalate":           False,
    },
    "incident": {
        "query_type":         "incident",
        "status_summary":     "ACTIVE INCIDENT — checkout-service DOWN, cascading to payment-service and api-gateway.",
        "narrative":          (
            "checkout-service v1.9.0 introduced a cache warm-up loading 250k records on startup. "
            "Memory peaked at 1.1Gi against a 512Mi limit, triggering an OOMKill. "
            "The pod restart loop is causing 503s that have cascaded to payment-service (8.7% error rate) "
            "and tripped the api-gateway circuit breaker on /checkout/**."
        ),
        "causal_chain":       [
            "deploy v1.9.0 — cache warm-up loads 250k records on startup",
            "startup memory spike: 1.1Gi peak vs 512Mi limit",
            "OOM killer terminates process → pod restart loop → sustained 503s",
            "payment-service calls to checkout time out → error rate rises to 8.7%",
            "api-gateway circuit breaker opens on /checkout/** → all checkout traffic blocked",
        ],
        "confidence":         "HIGH",
        "recommended_action": (
            "Immediate: roll back checkout-service to v1.8.x. "
            "Then increase memory limit to 2Gi before re-deploying v1.9.0. "
            "Page on-call — P1 incident."
        ),
        "deploy_safe":        False,
        "escalate":           True,
    },
}

# ── Phase 1 — Routing system prompt ────────────────────────────────────────────
# Short, precise prompt — classification only. max_tokens=64 is enough.
# The three query types map directly to how the agent fetches data in Phase 2.
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

Analyse the data and answer the query. Return ONLY valid JSON:
{
  "status_summary":     "<one sentence — current platform state>",
  "narrative":          "<2-4 sentences — plain English diagnosis, suitable for Slack>",
  "causal_chain":       ["<cause>", "<effect>", "..."],
  "confidence":         "HIGH | MEDIUM | LOW",
  "recommended_action": "<concrete next step — specific enough to act on immediately>",
  "deploy_safe":        true | false | null,
  "escalate":           true | false
}

Rules:
- causal_chain is ordered from root cause to visible symptom. Empty list [] if all healthy.
- deploy_safe is true only if all services are UP and no anomalies exist.
  null if the query is not about deploying.
- escalate is true when a P1/P2 incident is active or immediate human intervention is needed.
- confidence is HIGH when root cause is unambiguous from the data, MEDIUM when inferred.
- narrative must be readable by an engineer unfamiliar with the system.
"""


# ── Data fetching ──────────────────────────────────────────────────────────────

def fetch_endpoint(base_url: str, path: str) -> dict:
    """Fetch a single observability endpoint. Returns parsed JSON or an error dict."""
    try:
        with urllib.request.urlopen(f"{base_url}{path}", timeout=5) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.URLError as exc:
        return {"error": str(exc), "endpoint": path}


def fetch_platform_data(base_url: str) -> dict:
    """Fetch all four endpoints and return a combined snapshot."""
    return {
        "health":    fetch_endpoint(base_url, "/health"),
        "metrics":   fetch_endpoint(base_url, "/metrics"),
        "anomalies": fetch_endpoint(base_url, "/anomalies"),
        "events":    fetch_endpoint(base_url, "/events"),
    }


def detect_mock_scenario(platform_data: dict) -> str:
    """Identify which mock scenario is active from the platform data."""
    anomaly_count = platform_data.get("anomalies", {}).get("count", 0)
    services      = platform_data.get("health", {}).get("services", {})
    any_down      = any(s.get("status") == "DOWN" for s in services.values())
    if any_down or anomaly_count >= 3:
        return "incident"
    if anomaly_count >= 1:
        return "high-load"
    return "normal"


# ── Phase 1: Route ─────────────────────────────────────────────────────────────

def phase1_route(query: str) -> str:
    """
    Phase 1 — Classify the query type.

    Implementation notes:
    - max_tokens=64 is intentional: classification doesn't need generation.
      Using 64 instead of 1024 makes this step ~15x cheaper in token cost.
    - .get("query_type", "health_check") — the default handles any edge case
      where Claude doesn't return the expected key (e.g. empty response).
    - In mock mode, simple keyword matching avoids an API call while still
      demonstrating that the routing logic works correctly.

    Returns one of: "health_check" | "investigation" | "incident"
    """
    if MOCK_MODE:
        # Keyword-based routing for mock mode — no API call needed.
        # This mirrors what Claude does in real mode but deterministically.
        q = query.lower()
        if any(w in q for w in ["wrong", "down", "outage", "paged", "incident", "broken", "failing"]):
            return "incident"
        if any(w in q for w in ["slow", "latency", "elevated", "degraded", "scale", "high"]):
            return "investigation"
        return "health_check"

    # Real mode: one Claude call to classify the query.
    # The ROUTING_SYSTEM_PROMPT constrains the output to one key with three valid values.
    result = ask(
        system=ROUTING_SYSTEM_PROMPT,
        user=f'Query: "{query}"',
        model=MODEL,
        max_tokens=64,   # classification only — no generation needed
    )
    # Default to health_check if the key is missing — never crash on a routing failure
    return result.get("query_type", "health_check")


# ── Phase 2: Analyse ───────────────────────────────────────────────────────────

def phase2_analyse(query: str, query_type: str, platform_data: dict) -> dict:
    """
    Phase 2 — Analyse platform data and produce the structured response.

    Implementation notes:
    - The user_msg combines three things: the original query, the query type
      (so Claude knows what kind of answer to produce), and the raw platform
      data snapshot.
    - Passing query_type in the user message (not as a separate system instruction)
      lets Claude adapt its analysis style: incident queries get a causal chain
      and escalation recommendation; health_check queries get a simple status.
    - json.dumps(platform_data, indent=2) sends the full snapshot as readable
      JSON, which Claude can reason over field by field.

    Returns the structured analysis dict.
    """
    if MOCK_MODE:
        # In mock mode, select the pre-baked response for the current scenario.
        scenario = detect_mock_scenario(platform_data)
        return MOCK_RESPONSES[scenario].copy()

    # Build the user message: query context + query type + platform data
    user_msg = (
        f'Query: "{query}"\n'
        f'Query type: {query_type}\n\n'
        f'Platform data snapshot:\n{json.dumps(platform_data, indent=2)}'
    )
    return ask(
        system=ANALYSIS_SYSTEM_PROMPT,
        user=user_msg,
        model=MODEL,
        max_tokens=1024,
    )


# ── Main ───────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Module 6 Conversational Observability Agent — Solution")
    parser.add_argument("--query",  required=True, help='Natural-language query, e.g. "Is it safe to deploy?"')
    parser.add_argument("--server", default=DEFAULT_SERVER, help="Observability mock server base URL")
    parser.add_argument("--mock",   action="store_true",    help="Run in mock mode — no API key or server needed")
    args = parser.parse_args()

    print(f"[solution] Query  : {args.query}")
    print(f"[solution] Server : {args.server}")
    print(f"[solution] Mock   : {MOCK_MODE}\n")

    # ── Fetch platform data ─────────────────────────────────────────────────────
    if MOCK_MODE:
        # Load scenario data from the observability_mock module
        _mock_dir = str(Path(__file__).parent.parent)
        if _mock_dir not in sys.path:
            sys.path.insert(0, _mock_dir)
        from observability_mock import SCENARIOS  # noqa: E402
        scenario_key  = "incident"  # change to "normal" or "high-load" to see different output
        platform_data = SCENARIOS[scenario_key]
        print(f"[MOCK MODE] Using '{scenario_key}' scenario data (no server needed)\n")
    else:
        print(f"[solution] Fetching platform data from {args.server}...")
        platform_data = fetch_platform_data(args.server)
        errors = [k for k, v in platform_data.items() if "error" in v]
        if errors:
            print(f"⚠️  Could not reach endpoints: {errors}")
            print("   Is the mock server running?  python module6/observability_mock.py")
            sys.exit(1)

    # ── Phase 1: Route ──────────────────────────────────────────────────────────
    print("[Phase 1 — Route] Classifying query...")
    query_type = phase1_route(args.query)
    print(f"[Phase 1 — Route] query_type = {query_type}\n")

    # ── Phase 2: Analyse ────────────────────────────────────────────────────────
    print("[Phase 2 — Analyse] Running analysis...")
    analysis = phase2_analyse(args.query, query_type, platform_data)

    # ── Assemble final result ───────────────────────────────────────────────────
    result = {
        "query":             args.query,
        "query_type":        query_type,
        "timestamp":         datetime.now(timezone.utc).isoformat(),
        **analysis,
        "raw_platform_data": platform_data,
    }

    # ── Print summary ───────────────────────────────────────────────────────────
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
    print(to_step_summary(result, title="Module 6 Solution Response"))

    if result.get("escalate"):
        print("\n🔴 ESCALATION REQUIRED — GitHub Issue body:")
        print(to_github_issue(result, module=6))

    return result


if __name__ == "__main__":
    main()
