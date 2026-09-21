from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID

import pytest

from electronics_rfq_agent.procurement.domain.models import (
    Eligibility,
    IdentityRelation,
    OfferedIdentity,
    SourceEvidence,
    SupplierQuoteLine,
    SupplierRFQLine,
    SupplierRFQStatus,
)
from electronics_rfq_agent.procurement.domain.policy import evaluate_candidate
from electronics_rfq_agent.procurement.domain.state_machine import (
    InvalidSupplierRFQTransition,
    transition_supplier_rfq,
)


RFQ_LINE_ID = UUID("00000000-0000-0000-0000-000000000001")
QUOTE_ID = UUID("00000000-0000-0000-0000-000000000010")
DOCUMENT_ID = UUID("00000000-0000-0000-0000-000000000100")
QUOTE_LINE_ID = UUID("00000000-0000-0000-0000-000000000200")


def requested_line() -> SupplierRFQLine:
    return SupplierRFQLine(
        id=RFQ_LINE_ID,
        line_no=1,
        requested_part_number="S203-C16",
        manufacturer="ABB",
        quantity=Decimal("100"),
        uom="PCS",
        substitutions_allowed=False,
    )


def evidence(
    value: str,
    *,
    document_id: UUID = DOCUMENT_ID,
    row: int = 2,
) -> SourceEvidence:
    return SourceEvidence(
        document_id=document_id,
        sha256="a" * 64,
        filename="supplier-offer.xlsx",
        mime_type=(
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        ),
        fact_key="unit_price",
        sheet="Offer",
        row=row,
        original_value=value,
        normalized_value=value,
        extractor="golden-fixture",
        extracted_at=datetime(2026, 9, 21, tzinfo=timezone.utc),
        confidence=1.0,
    )


def quote_line(
    *,
    relation: IdentityRelation,
    moq: Decimal | None = None,
    quote_evidence: tuple[SourceEvidence, ...] | None = None,
) -> SupplierQuoteLine:
    return SupplierQuoteLine(
        id=QUOTE_LINE_ID,
        supplier_quote_id=QUOTE_ID,
        supplier_rfq_line_id=RFQ_LINE_ID,
        offered_identity=OfferedIdentity(
            manufacturer="ABB",
            manufacturer_part_number="S203-C16",
            relation=relation,
            confidence=1.0,
        ),
        quoted_quantity=Decimal("100"),
        uom="PCS",
        moq=moq,
        unit_price=Decimal("7.91"),
        currency="EUR",
        stock_qty=Decimal("100"),
        lead_time_days=2,
        evidence=quote_evidence or (evidence("7.91"),),
    )


def test_g001_exact_match_is_eligible() -> None:
    result, reasons = evaluate_candidate(
        requested_line(),
        quote_line(relation=IdentityRelation.EXACT),
    )

    assert result is Eligibility.ELIGIBLE
    assert reasons == ()


def test_g002_substitute_requires_review() -> None:
    result, reasons = evaluate_candidate(
        requested_line(),
        quote_line(relation=IdentityRelation.SUBSTITUTE),
    )

    assert result is Eligibility.REVIEW_REQUIRED
    assert "IDENTITY_SUBSTITUTE" in reasons


def test_g003_moq_mismatch_requires_review() -> None:
    result, reasons = evaluate_candidate(
        requested_line(),
        quote_line(
            relation=IdentityRelation.EXACT,
            moq=Decimal("500"),
        ),
    )

    assert result is Eligibility.REVIEW_REQUIRED
    assert "MOQ_EXCEEDS_REQUESTED_QUANTITY" in reasons


def test_g004_conflicting_evidence_requires_review() -> None:
    second_document = UUID("00000000-0000-0000-0000-000000000101")
    result, reasons = evaluate_candidate(
        requested_line(),
        quote_line(
            relation=IdentityRelation.EXACT,
            quote_evidence=(
                evidence("7.91"),
                evidence("8.19", document_id=second_document, row=3),
            ),
        ),
    )

    assert result is Eligibility.REVIEW_REQUIRED
    assert "CONFLICTING_EVIDENCE" in reasons


def test_supplier_rfq_cannot_be_sent_without_supplier() -> None:
    with pytest.raises(
        InvalidSupplierRFQTransition,
        match="at least one supplier",
    ):
        transition_supplier_rfq(
            SupplierRFQStatus.READY,
            SupplierRFQStatus.SENT,
            line_count=1,
            supplier_count=0,
        )


def test_supplier_rfq_rejects_illegal_transition() -> None:
    with pytest.raises(InvalidSupplierRFQTransition):
        transition_supplier_rfq(
            SupplierRFQStatus.DRAFT,
            SupplierRFQStatus.AWARDED,
            line_count=1,
            supplier_count=3,
        )
