from datetime import datetime
from decimal import Decimal
from uuid import UUID, uuid4

import pytest
from pydantic import ValidationError

from electronics_rfq_agent.supplier_intelligence import (
    SupplierCandidate,
    SupplierEvidence,
    evaluate_supplier_candidates,
)


def _candidate(
    supplier_id: str,
    *,
    price: str = "10.00",
    qty: int = 100,
    lead_time_days: int = 5,
    compliance_ok: bool = True,
    confidence: float = 0.95,
) -> SupplierCandidate:
    return SupplierCandidate(
        supplier_id=supplier_id,
        unit_price=Decimal(price),
        available_qty=qty,
        lead_time_days=lead_time_days,
        compliance_ok=compliance_ok,
        confidence=confidence,
        evidence_ids=[uuid4()],
    )


def test_supplier_evidence_requires_timezone_aware_timestamp() -> None:
    with pytest.raises(ValidationError):
        SupplierEvidence(
            supplier_id="SUP-1",
            evidence_type="price",
            source="catalog",
            source_record_id="price-1",
            retrieved_at=datetime(2026, 9, 19, 12, 0, 0),
            value=Decimal("10.00"),
            confidence=0.9,
        )


def test_no_candidates_returns_no_supplier_found() -> None:
    decision = evaluate_supplier_candidates(
        rfq_line_id="RFQ-1-L1",
        product_id="ABB:S203-C16",
        requested_qty=10,
        candidates=[],
    )

    assert decision.outcome == "NO_SUPPLIER_FOUND"
    assert decision.selected_supplier_id is None
    assert decision.confidence == 0.0
    assert decision.evidence_ids == []


def test_ineligible_candidates_require_review() -> None:
    candidates = [
        _candidate("SUP-NONCOMPLIANT", compliance_ok=False),
        _candidate("SUP-LOW-CONFIDENCE", confidence=0.50),
        _candidate("SUP-NO-STOCK", qty=1),
    ]

    decision = evaluate_supplier_candidates(
        rfq_line_id="RFQ-1-L1",
        product_id="ABB:S203-C16",
        requested_qty=10,
        candidates=candidates,
    )

    assert decision.outcome == "REVIEW_REQUIRED"
    assert decision.selected_supplier_id is None
    assert set(decision.candidate_supplier_ids) == {
        "SUP-NONCOMPLIANT",
        "SUP-LOW-CONFIDENCE",
        "SUP-NO-STOCK",
    }


def test_policy_selects_lowest_price_among_eligible_candidates() -> None:
    expensive_fast = _candidate(
        "SUP-A",
        price="12.00",
        lead_time_days=1,
        confidence=0.99,
    )
    cheap_slow = _candidate(
        "SUP-B",
        price="10.00",
        lead_time_days=7,
        confidence=0.90,
    )

    decision = evaluate_supplier_candidates(
        rfq_line_id="RFQ-1-L1",
        product_id="ABB:S203-C16",
        requested_qty=10,
        candidates=[expensive_fast, cheap_slow],
    )

    assert decision.outcome == "ACCEPTED"
    assert decision.selected_supplier_id == "SUP-B"
    assert decision.confidence == 0.90
    assert all(isinstance(evidence_id, UUID) for evidence_id in decision.evidence_ids)


def test_equal_price_prefers_shorter_lead_time() -> None:
    slow = _candidate("SUP-SLOW", price="10.00", lead_time_days=10)
    fast = _candidate("SUP-FAST", price="10.00", lead_time_days=2)

    decision = evaluate_supplier_candidates(
        rfq_line_id="RFQ-1-L1",
        product_id="ABB:S203-C16",
        requested_qty=10,
        candidates=[slow, fast],
    )

    assert decision.outcome == "ACCEPTED"
    assert decision.selected_supplier_id == "SUP-FAST"


@pytest.mark.parametrize("requested_qty", [0, -1])
def test_requested_quantity_must_be_positive(requested_qty: int) -> None:
    with pytest.raises(ValueError, match="requested_qty"):
        evaluate_supplier_candidates(
            rfq_line_id="RFQ-1-L1",
            product_id="ABB:S203-C16",
            requested_qty=requested_qty,
            candidates=[_candidate("SUP-1")],
        )
