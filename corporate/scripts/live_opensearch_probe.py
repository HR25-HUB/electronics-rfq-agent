from __future__ import annotations

import json
import os
import sys

import httpx

from corporate_rfq.live_probe import redacted_probe_output, run_live_probe


def required_env(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise RuntimeError(f"Required environment variable is not configured: {name}")
    return value


def main() -> int:
    try:
        base_url = required_env("OPENSEARCH_URL")
        raw_line = required_env("RFQ_LIVE_PROBE_LINE")
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        return 2

    headers: dict[str, str] = {}
    authorization = os.environ.get("OPENSEARCH_AUTHORIZATION", "").strip()
    if authorization:
        headers["Authorization"] = authorization

    try:
        timeout_seconds = float(os.environ.get("OPENSEARCH_TIMEOUT_SECONDS", "10"))
    except ValueError:
        print("OPENSEARCH_TIMEOUT_SECONDS must be numeric", file=sys.stderr)
        return 2

    if timeout_seconds <= 0 or timeout_seconds > 30:
        print("OPENSEARCH_TIMEOUT_SECONDS must be > 0 and <= 30", file=sys.stderr)
        return 2

    try:
        with httpx.Client(
            base_url=base_url,
            headers=headers,
            timeout=timeout_seconds,
            follow_redirects=False,
        ) as client:
            summary = run_live_probe(client=client, raw_line=raw_line)
    except Exception as exc:
        # Do not print request bodies, response bodies, raw RFQ content or headers.
        print(f"Live read probe failed: {type(exc).__name__}", file=sys.stderr)
        return 3

    print(json.dumps(redacted_probe_output(summary), ensure_ascii=False, indent=2))
    return 0 if summary.outcome_kind == "decision" else 4


if __name__ == "__main__":
    raise SystemExit(main())
