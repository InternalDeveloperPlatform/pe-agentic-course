"""
module6/observability_mock.py
Observability Mock Server — Module 6 exercise companion.

Simulates a real observability platform (think Datadog / Prometheus / PagerDuty)
by serving realistic platform health data from a local HTTP server.

We can't connect to real production systems in a course exercise, so this mock
server gives the conversational agent realistic data to reason about.

Usage
-----
    python module6/observability_mock.py                          # normal scenario
    python module6/observability_mock.py --scenario incident      # active incident
    python module6/observability_mock.py --scenario high-load     # elevated traffic
    python module6/observability_mock.py --port 9090              # custom port (default: 8080)

Available endpoints (all return JSON)
--------------------------------------
    GET /health       — per-service health status (UP / DEGRADED / DOWN)
    GET /metrics      — error rates, latency, throughput, memory usage
    GET /anomalies    — detected anomalies with severity and correlation chain
    GET /events       — recent deployment and config-change events

Scenarios
---------
    normal      All services healthy. Safe to deploy.
    high-load   Elevated traffic, some latency increase. No anomalies.
    incident    OOMKill in checkout-service. Cascading 503s. 3 correlated anomalies.

The --scenario flag is the key demo tool: switch from normal → incident mid-session
and watch the conversational agent immediately reframe its response.
"""

import json
import argparse
from http.server import HTTPServer, BaseHTTPRequestHandler
from datetime import datetime, timezone

# ── Scenario data ──────────────────────────────────────────────────────────────

SCENARIOS = {
    "normal": {
        "health": {
            "timestamp": "2026-04-03T10:00:00Z",
            "services": {
                "api-gateway":      {"status": "UP",   "uptime_pct": 99.98, "latency_ms": 42},
                "checkout-service": {"status": "UP",   "uptime_pct": 99.99, "latency_ms": 87},
                "payment-service":  {"status": "UP",   "uptime_pct": 100.0, "latency_ms": 124},
                "user-service":     {"status": "UP",   "uptime_pct": 99.97, "latency_ms": 31},
                "inventory-service":{"status": "UP",   "uptime_pct": 99.95, "latency_ms": 58},
            },
        },
        "metrics": {
            "timestamp": "2026-04-03T10:00:00Z",
            "error_rate_pct": 0.02,
            "requests_per_second": 1240,
            "p50_latency_ms": 45,
            "p95_latency_ms": 180,
            "p99_latency_ms": 420,
            "memory_usage_pct": 62,
            "cpu_usage_pct": 38,
            "active_deployments": 0,
        },
        "anomalies": {
            "timestamp": "2026-04-03T10:00:00Z",
            "count": 0,
            "items": [],
        },
        "events": {
            "timestamp": "2026-04-03T10:00:00Z",
            "recent_events": [
                {"time": "2026-04-02T22:14:00Z", "type": "deployment", "service": "user-service",      "version": "v2.3.1", "status": "success"},
                {"time": "2026-04-02T18:30:00Z", "type": "config_change", "service": "api-gateway",   "change": "rate_limit increased to 5000 rps", "author": "maya@example.com"},
                {"time": "2026-04-01T09:00:00Z", "type": "deployment", "service": "payment-service",  "version": "v4.1.0", "status": "success"},
            ],
        },
    },

    "high-load": {
        "health": {
            "timestamp": "2026-04-03T10:00:00Z",
            "services": {
                "api-gateway":      {"status": "UP",       "uptime_pct": 99.91, "latency_ms": 210},
                "checkout-service": {"status": "DEGRADED", "uptime_pct": 99.60, "latency_ms": 680},
                "payment-service":  {"status": "UP",       "uptime_pct": 99.88, "latency_ms": 340},
                "user-service":     {"status": "UP",       "uptime_pct": 99.95, "latency_ms": 75},
                "inventory-service":{"status": "UP",       "uptime_pct": 99.99, "latency_ms": 90},
            },
        },
        "metrics": {
            "timestamp": "2026-04-03T10:00:00Z",
            "error_rate_pct": 1.8,
            "requests_per_second": 4100,
            "p50_latency_ms": 210,
            "p95_latency_ms": 820,
            "p99_latency_ms": 2100,
            "memory_usage_pct": 84,
            "cpu_usage_pct": 78,
            "active_deployments": 0,
        },
        "anomalies": {
            "timestamp": "2026-04-03T10:00:00Z",
            "count": 1,
            "items": [
                {
                    "id": "anom-001",
                    "severity": "MEDIUM",
                    "service": "checkout-service",
                    "description": "P95 latency 4.5x baseline — consistent with traffic spike, not code regression.",
                    "detected_at": "2026-04-03T09:51:00Z",
                    "correlated_events": [],
                }
            ],
        },
        "events": {
            "timestamp": "2026-04-03T10:00:00Z",
            "recent_events": [
                {"time": "2026-04-03T09:00:00Z", "type": "traffic_spike", "detail": "Marketing campaign launched — 3.3x normal traffic"},
                {"time": "2026-04-02T22:14:00Z", "type": "deployment", "service": "user-service", "version": "v2.3.1", "status": "success"},
            ],
        },
    },

    "incident": {
        "health": {
            "timestamp": "2026-04-03T10:00:00Z",
            "services": {
                "api-gateway":      {"status": "DEGRADED", "uptime_pct": 97.20, "latency_ms": 1840},
                "checkout-service": {"status": "DOWN",     "uptime_pct": 72.10, "latency_ms": None},
                "payment-service":  {"status": "DEGRADED", "uptime_pct": 94.80, "latency_ms": 2100},
                "user-service":     {"status": "UP",       "uptime_pct": 99.95, "latency_ms": 38},
                "inventory-service":{"status": "UP",       "uptime_pct": 99.99, "latency_ms": 62},
            },
        },
        "metrics": {
            "timestamp": "2026-04-03T10:00:00Z",
            "error_rate_pct": 12.4,
            "requests_per_second": 890,
            "p50_latency_ms": 1200,
            "p95_latency_ms": 4800,
            "p99_latency_ms": 12000,
            "memory_usage_pct": 97,
            "cpu_usage_pct": 91,
            "active_deployments": 1,
            "recent_deploy": {
                "deploy_id":    "deploy-2026-0403-007",
                "service":      "checkout-service",
                "version":      "v1.9.0",
                "deployed_at":  "2026-04-03T09:42:00Z",
                "deploy_age_minutes": 18,
            },
        },
        "anomalies": {
            "timestamp": "2026-04-03T10:00:00Z",
            "count": 3,
            "items": [
                {
                    "id": "anom-101",
                    "severity": "CRITICAL",
                    "service": "checkout-service",
                    "description": "OOMKill detected: process killed by kernel OOM killer (signal 9). Memory peaked at 1.1Gi against a 512Mi limit.",
                    "detected_at": "2026-04-03T09:43:12Z",
                    "correlated_events": ["deploy-2026-0403-007"],
                    "causal_chain": "deploy v1.9.0 introduced cache warm-up loading 250k records → memory spike → OOMKill → pod restart loop → 503s",
                },
                {
                    "id": "anom-102",
                    "severity": "HIGH",
                    "service": "payment-service",
                    "description": "Error rate spike from 0.1% to 8.7% — consistent with upstream 503s from checkout-service dependency calls timing out.",
                    "detected_at": "2026-04-03T09:44:30Z",
                    "correlated_events": ["anom-101"],
                    "causal_chain": "checkout OOMKill → payment service dependency calls failing → cascading error rate spike",
                },
                {
                    "id": "anom-103",
                    "severity": "HIGH",
                    "service": "api-gateway",
                    "description": "Circuit breaker opened on checkout-service route. Returning 503 for all /checkout/** requests.",
                    "detected_at": "2026-04-03T09:45:08Z",
                    "correlated_events": ["anom-101", "anom-102"],
                    "causal_chain": "checkout 503s → api-gateway circuit breaker trips → all checkout traffic blocked",
                },
            ],
        },
        "events": {
            "timestamp": "2026-04-03T10:00:00Z",
            "recent_events": [
                {"time": "2026-04-03T09:42:00Z", "type": "deployment", "service": "checkout-service", "version": "v1.9.0", "status": "deployed", "note": "Added 250k-record order cache warm-up on startup"},
                {"time": "2026-04-03T09:43:12Z", "type": "oomkill",    "service": "checkout-service", "pid": 7831, "memory_limit_mi": 512, "memory_peak_mi": 1126},
                {"time": "2026-04-03T09:45:08Z", "type": "circuit_breaker_open", "service": "api-gateway", "route": "/checkout/**"},
                {"time": "2026-04-03T09:47:00Z", "type": "alert_fired", "alert": "checkout-service-down", "severity": "P1", "pagerduty_incident": "INC-20847"},
            ],
        },
    },
}

VALID_SCENARIOS = list(SCENARIOS.keys())


class ObservabilityHandler(BaseHTTPRequestHandler):
    """HTTP request handler for the observability mock server."""

    scenario: str = "normal"  # set before serving

    def _send_json(self, data: dict, status: int = 200) -> None:
        body = json.dumps(data, indent=2).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _not_found(self) -> None:
        self._send_json({
            "error": f"Unknown endpoint: {self.path}",
            "available_endpoints": ["/health", "/metrics", "/anomalies", "/events"],
        }, status=404)

    def do_GET(self) -> None:  # noqa: N802
        scenario_data = SCENARIOS[self.scenario]
        path = self.path.rstrip("/")

        if path == "/health":
            self._send_json(scenario_data["health"])
        elif path == "/metrics":
            self._send_json(scenario_data["metrics"])
        elif path == "/anomalies":
            self._send_json(scenario_data["anomalies"])
        elif path == "/events":
            self._send_json(scenario_data["events"])
        else:
            self._not_found()

    def log_message(self, fmt: str, *args) -> None:  # noqa: ANN001
        # Suppress default HTTP logging — cleaner terminal for demos
        ts = datetime.now(timezone.utc).strftime("%H:%M:%S")
        print(f"[mock] {ts}  {fmt % args}")


def main():
    parser = argparse.ArgumentParser(description="Module 6 Observability Mock Server")
    parser.add_argument(
        "--scenario",
        choices=VALID_SCENARIOS,
        default="normal",
        help=f"Observability scenario to serve (default: normal). Options: {', '.join(VALID_SCENARIOS)}",
    )
    parser.add_argument("--port", type=int, default=8080, help="Port to listen on (default: 8080)")
    args = parser.parse_args()

    ObservabilityHandler.scenario = args.scenario

    print(f"\n[observability_mock] Starting mock server")
    print(f"  Scenario : {args.scenario}")
    print(f"  Port     : {args.port}")
    print(f"  Endpoints: /health  /metrics  /anomalies  /events")
    print(f"\n  Example:")
    print(f"    curl -s http://localhost:{args.port}/health | python -m json.tool")
    print(f"\n  Press Ctrl+C to stop.\n")

    server = HTTPServer(("0.0.0.0", args.port), ObservabilityHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[observability_mock] Shutting down.")
        server.server_close()


if __name__ == "__main__":
    main()
