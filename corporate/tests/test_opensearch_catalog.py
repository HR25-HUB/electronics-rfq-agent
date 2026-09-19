# ruff: noqa: I001
from __future__ import annotations

import json
from pathlib import Path

import pytest

from corporate_rfq.models import CatalogUnavailable, NormalizedRFQLine
from corporate_rfq.opensearch_catalog import (
    CATALOG_INDEX,
    OpenSearchCatalogReadOnlyAdapter,
    OpenSearchTransportError,
    build_candidate_body,
    build_exact_lookup_body,
)


FIXTURE = Path(__file__).parent / "fixtures" / "opensearch_catalog_response.json"


class FixtureSearchTransport:
    def __init__(self, *, fail: bool = False) -> None:
        self.fail = fail
        self.calls: list[tuple[str, dict[str, object]]] = []
        self.payload = json.loads(FIXTURE.read_text(encoding="utf-8"))

    def search(self, *, index: str, body: dict[str, object]) -> dict[str, object]:
        self.calls.append((index, body))
        if self.fail:
            raise OpenSearchTransportError("fixture outage")
        return self.payload


def line() -> NormalizedRFQLine:
    return NormalizedRFQLine(
        rfq_id="RFQ-OS-1",
        line_id="1",
        raw_text="ABB S203-C16 breaker 3P 16A — 5 pcs",
        manufacturer="ABB",
        part_number_normalized="S203C16",
        quantity=5,
        uom="pcs",
        category="circuit_breaker",
        attributes={"poles": "3P", "current": "16A"},
    )


def test_exact_lookup_uses_catalog_index_and_validates_normalized_sku() -> None:
    transport = FixtureSearchTransport()
    adapter = OpenSearchCatalogReadOnlyAdapter(transport)

    product = adapter.find_normalized_exact(
        normalized_mpn="S203C16",
        manufacturer="ABB",
    )

    assert product is not None
    assert product.product_id == "ABB:S203-C16"
    assert product.attributes["poles"] == "3P"
    assert transport.calls[0][0] == CATALOG_INDEX


def test_exact_lookup_query_is_read_only_search_body() -> None:
    body = build_exact_lookup_body("S203C16")

    assert body["size"] == 5
    assert body["query"]["match"]["sku"]["query"] == "S203C16"
    assert not any(key in body for key in ("script", "update", "delete", "index"))


def test_candidate_query_uses_documented_catalog_fields() -> None:
    body = build_candidate_body(line(), limit=3)
    serialized = json.dumps(body)

    assert body["size"] == 3
    for field in ("sku", "brand", "category", "attributes"):
        assert field in serialized


def test_candidate_mapping_preserves_raw_opensearch_score_as_evidence_only() -> None:
    adapter = OpenSearchCatalogReadOnlyAdapter(FixtureSearchTransport())

    candidates = adapter.retrieve_candidates(line(), limit=1)

    assert len(candidates) == 1
    assert candidates[0].product.product_id == "ABB:S203-C16"
    assert candidates[0].score == 0.0
    evidence = {(item.key, item.value) for item in candidates[0].evidence}
    assert ("raw_score", "12.75") in evidence
    assert ("index", CATALOG_INDEX) in evidence


@pytest.mark.parametrize("operation", ["exact", "candidate"])
def test_transport_failure_becomes_catalog_unavailable(operation: str) -> None:
    adapter = OpenSearchCatalogReadOnlyAdapter(FixtureSearchTransport(fail=True))

    with pytest.raises(CatalogUnavailable):
        if operation == "exact":
            adapter.find_normalized_exact(
                normalized_mpn="S203C16",
                manufacturer="ABB",
            )
        else:
            adapter.retrieve_candidates(line())


def test_public_adapter_surface_is_read_only() -> None:
    forbidden = ("create", "update", "delete", "write", "save", "upsert", "mutate", "bulk")
    public_names = {
        name
        for name in dir(OpenSearchCatalogReadOnlyAdapter)
        if not name.startswith("_")
    }

    assert not any(name.startswith(forbidden) for name in public_names)
