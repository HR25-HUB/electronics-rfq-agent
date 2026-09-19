from __future__ import annotations

from typing import Any
from uuid import UUID

import pytest

from corporate_rfq.opensearch_catalog import OpenSearchTransportError
from corporate_rfq.retrieval_evidence import (
    EvidenceRecordingOpenSearchTransport,
    InMemoryRetrievalEvidenceSink,
    canonical_query_sha256,
)


class StubTransport:
    def __init__(self, *, fail: bool = False) -> None:
        self.fail = fail

    def search(self, *, index: str, body: dict[str, Any]) -> dict[str, Any]:
        if self.fail:
            raise OpenSearchTransportError("stub outage")
        return {
            "took": 7,
            "timed_out": False,
            "hits": {
                "hits": [
                    {"_id": "a"},
                    {"_id": "b"},
                ]
            },
        }


def test_query_hash_is_stable_across_key_order() -> None:
    left = {"query": {"bool": {"must": [{"term": {"brand": "ABB"}}]}}, "size": 5}
    right = {"size": 5, "query": {"bool": {"must": [{"term": {"brand": "ABB"}}]}}}

    assert canonical_query_sha256(left) == canonical_query_sha256(right)


def test_success_evidence_records_metadata_without_query_content() -> None:
    sink = InMemoryRetrievalEvidenceSink()
    trace_id = UUID("12345678-1234-5678-1234-567812345678")
    transport = EvidenceRecordingOpenSearchTransport(
        StubTransport(),
        sink,
        trace_id=trace_id,
    )
    body = {"query": {"match": {"sku": {"query": "S203C16"}}}}

    response = transport.search(index="gamm_catalog_products", body=body)

    assert response["took"] == 7
    assert len(sink.items) == 1
    evidence = sink.items[0]
    assert evidence.trace_id == trace_id
    assert evidence.index == "gamm_catalog_products"
    assert evidence.outcome == "success"
    assert evidence.hit_count == 2
    assert evidence.took_ms == 7
    assert evidence.timed_out is False
    assert evidence.query_sha256 == canonical_query_sha256(body)

    dumped = evidence.model_dump(mode="json")
    assert "query" not in dumped
    assert "response" not in dumped
    assert "S203C16" not in str(dumped)


def test_failure_evidence_records_error_class_and_reraises() -> None:
    sink = InMemoryRetrievalEvidenceSink()
    transport = EvidenceRecordingOpenSearchTransport(
        StubTransport(fail=True),
        sink,
    )

    with pytest.raises(OpenSearchTransportError):
        transport.search(
            index="gamm_catalog_products",
            body={"query": {"match_all": {}}},
        )

    assert len(sink.items) == 1
    evidence = sink.items[0]
    assert evidence.outcome == "failure"
    assert evidence.hit_count == 0
    assert evidence.error_class == "OpenSearchTransportError"
