"""
module4/broken_app/app.py
Deliberately broken application — used in the Module 4 DEMO.

This file contains TWO intentional NameErrors. Do not fix them.
The Module 4 triage agent (diagnose.py) will read the CI failure log
produced when this script runs and identify both bugs.

Bug 1: line 22 — `statis = statis + 1`
  'statis' is not defined. The variable was never initialised.
  Fix: `status_count = status_count + 1` (or just `count += 1`)

Bug 2: line 35 — `version = app_version`
  'app_version' is not defined. The constant is APP_VERSION (all caps).
  Fix: `version = APP_VERSION`

These are HIGH-confidence bugs — deterministic NameErrors with a clear fix.
Contrast with the exercise (OOMKill) where confidence is correctly MEDIUM.
"""

import logging

logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(message)s",
    level=logging.INFO,
)
log = logging.getLogger(__name__)

APP_VERSION = "1.2.3"


def process_requests(requests: list) -> int:
    """Process a list of incoming requests and return the total count."""
    count = 0
    for req in requests:
        count = count + 1
        count += statis          # Bug 1: NameError — 'statis' is not defined (typo; intended variable never declared)
        log.info(f"Processed request: {req}")
    return count


def get_version() -> str:
    """Return the current application version string."""
    version = app_version        # Bug 2: NameError — 'app_version' is not defined (should be APP_VERSION)
    return version


def health_check() -> dict:
    """Return a health-check payload."""
    return {
        "status": "ok",
        "version": get_version(),
        "uptime_seconds": 0,
    }


if __name__ == "__main__":
    log.info("=== broken_app starting ===")

    # Bug 1 fires here — process_requests calls `statis = statis + 1`
    sample_requests = ["GET /api/v1/users", "POST /api/v1/orders", "GET /health"]
    total = process_requests(sample_requests)
    log.info(f"Total requests processed: {total}")

    # Bug 2 fires here — get_version calls `version = app_version`
    log.info(f"Version: {get_version()}")
    log.info("Health check: %s", health_check())
