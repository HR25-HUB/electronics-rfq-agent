from __future__ import annotations

import json

import httpx

from corporate_rfq.live_probe import redacted_probe_output, run_live_probe


def test_live_probe_returns_decision_and_non_content_evidence() -> None:
    raw_line = "ABB S203-C16 breaker 3P 16A — 5 pcs"

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/gamm_catalog_products/_search"
        return httpx.Response(
            200,
            json={
                "took": 4,
                "timed_out": False,
                "hits": {
                    "hits": [
                        {
                            "_id": "abb-s203-c16",
                            "_score": 12.75,
                            "_source": {
                                "id": "ABB:S203-C16",
                                "sku": "S203-C16",
                                "name": "ABB S203-C16 circuit breaker 3P C16",
                                "brand": "ABB",
                                "category": "circuit_breaker",
                                "attributes": [
                                    {"key": "poles", "value": "3P"},
                                    {"key": "current", "value": "16A"},
                                    {"key": "curve", "value": "C"},
                                ],
                            },
                        }
                    ]
                },
            },
            request=request,
        )

    with httpx.Client(
        base_url="https://opensearch.invalid",
        transport=httpx.MockTransport(handler),
    ) as client:
        summary = run_live_probe(client=client, raw_line=raw_line)

    output = redacted_probe_output(summary)
    serialized = json.dumps(output, ensure_ascii=False)

    assert summary.outcome_kind == "decision"
    assert summary.decision_status == "ACCEPT"
    assert summary.canonical_product_id == "ABB:S203-C16"
    assert len(summary.evidence) == 1
    assert raw_line not in serialized
    assert "query" not in output
    assert "response" not in output


def test_live_probe_is_restricted_to_documented_catalog_index() -> None:
    with httpx.Client(base_url="https://opensearch.invalid") as client:
        try:
            run_live_probe(
                client=client,
                raw_line="ABB S203-C16 breaker 3P 16A — 5 pcs",
                index="other_index",
            )
        except ValueError as exc:
            assert "gamm_catalog_products" in str(exc)
        else:
            raise AssertionError("Expected live probe to reject non-catalog index")
