# ruff: noqa: I001
from __future__ import annotations

import json
from pathlib import Path

import pytest

from corporate_rfq.catalog_app import (
    CatalogAppCandidateDTO,
    CatalogAppProductDTO,
    CatalogAppReadOnlyAdapter,
    CatalogAppTransportError,
)
from corporate_rfq.models import CatalogUnavailable, NormalizedRFQLine


FIXTURE = Path(__file__).parent / "fixtures" / "catalog_app_products.json"


class FixtureTransport:
    def __init__(self, *, fail: bool = False) -> None:
        self.fail = fail
        payload = json.loads(FIXTURE.read_text(encoding="utf-8"))
        self.products = [CatalogAppProductDTO.model_validate(item) for item in payload]
        self.calls: list[tuple[str, object]] = []

    def get_by_normalized_mpn(self, normalized_mpn: str) -> CatalogAppProductDTO | None:
        self.calls.append(("get_by_normalized_mpn", normalized_mpn))
        if self.fail:
            raise CatalogAppTransportError("fixture outage")
        for product in self.products:
            if product.sku.replace("-", "").upper() == normalized_mpn:
                return product
        return None

    def search_candidates(
        self,
        *,
        manufacturer: str | None,
        normalized_mpn: str | None,
        category: str | None,
        attributes: dict[str, str],
        limit: int,
    ) -> list[CatalogAppCandidateDTO]:
        self.calls.append(
            (
                "search_candidates",
                {
                    "manufacturer": manufacturer,
                    "normalized_mpn": normalized_mpn,
                    "category": category,
                    "attributes": attributes,
                    "limit": limit,
                },
            )
        )
        if self.fail:
            raise CatalogAppTransportError("fixture outage")

        return [
            CatalogAppCandidateDTO(
                product=product,
                score=0.91 - index * 0.05,
                matched_by="fixture-hybrid-search",
            )
            for index, product in enumerate(self.products[:limit])
        ]


def test_exact_lookup_maps_catalog_app_read_model() -> None:
    transport = FixtureTransport()
    adapter = CatalogAppReadOnlyAdapter(transport)

    product = adapter.find_normalized_exact(
        normalized_mpn="S203C16",
        manufacturer="ABB",
    )

    assert product is not None
    assert product.product_id == "ABB:S203-C16"
    assert product.attributes["poles"] == "3P"
    assert transport.calls == [("get_by_normalized_mpn", "S203C16")]


def test_exact_lookup_rejects_manufacturer_mismatch() -> None:
    adapter = CatalogAppReadOnlyAdapter(FixtureTransport())

    product = adapter.find_normalized_exact(
        normalized_mpn="S203C16",
        manufacturer="Schneider Electric",
    )

    assert product is None


def test_candidate_retrieval_preserves_evidence_and_limit() -> None:
    transport = FixtureTransport()
    adapter = CatalogAppReadOnlyAdapter(transport)
    line = NormalizedRFQLine(
        rfq_id="RFQ-1",
        line_id="1",
        raw_text="ABB breaker 3P 16A — 5 pcs",
        manufacturer="ABB",
        part_number_normalized=None,
        quantity=5,
        uom="pcs",
        category="circuit_breaker",
        attributes={"poles": "3P", "current": "16A"},
    )

    candidates = adapter.retrieve_candidates(line, limit=1)

    assert len(candidates) == 1
    assert candidates[0].product.product_id == "ABB:S203-C16"
    assert candidates[0].evidence[0].source == "catalog.app"
    assert candidates[0].evidence[0].key == "matched_by"


@pytest.mark.parametrize("method", ["exact", "search"])
def test_transport_failure_becomes_catalog_unavailable(method: str) -> None:
    adapter = CatalogAppReadOnlyAdapter(FixtureTransport(fail=True))

    with pytest.raises(CatalogUnavailable):
        if method == "exact":
            adapter.find_normalized_exact(
                normalized_mpn="S203C16",
                manufacturer="ABB",
            )
        else:
            adapter.retrieve_candidates(
                NormalizedRFQLine(
                    rfq_id="RFQ-2",
                    line_id="1",
                    raw_text="ABB breaker 3P 16A — 5 pcs",
                    manufacturer="ABB",
                    quantity=5,
                    uom="pcs",
                    category="circuit_breaker",
                )
            )


def test_public_adapter_surface_is_read_only() -> None:
    forbidden_prefixes = ("create", "update", "delete", "write", "save", "upsert", "mutate")
    public_names = {name for name in dir(CatalogAppReadOnlyAdapter) if not name.startswith("_")}

    assert not any(name.startswith(forbidden_prefixes) for name in public_names)
