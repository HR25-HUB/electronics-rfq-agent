from __future__ import annotations

import uuid
from datetime import datetime, timezone
from decimal import Decimal

import pytest

from electronics_rfq_agent.procurement.domain.models import (
    AwardDecision,
    AwardOutcome,
    AwardReason,
    CommercialComparison,
    ComparisonCandidate,
    Eligibility,
    IdentityRelation,
    OfferedIdentity,
    SourceEvidence,
    SupplierQuote,
    SupplierQuoteLine,
    SupplierQuoteStatus,
    SupplierRFQLine,
    SupplierRFQStatus,
)
from electronics_rfq_agent.procurement.domain.policy import evaluate_candidate
from electronics_rfq_agent.procurement.domain.state_machine import (
    InvalidSupplierRFQTransitionError,
    transition_supplier_rfq,
)

RFQ_LINE_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")
QUOTE_ID = uuid.UUID("00000000-0000-0000-0000-000000000010")
DOCUMENT_ID = uuid.UUID("00000000-0000-0000-0000-000000000100")
QUOTE_LINE_ID = uuid.UUID("00000000-0000-0000-0000-000000000200")


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
    document_id: uuid.UUID = DOCUMENT_ID,
    row: int = 2,
) -> SourceEvidence:
    return SourceEvidence(
        document_id=document_id,
        sha256="a" * 64,
        filename="supplier-offer.xlsx",
        mime_type=("application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"),
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
        evidence=(evidence("7.91"),) if quote_evidence is None else quote_evidence,
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
    second_document = uuid.UUID("00000000-0000-0000-0000-000000000101")
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
        InvalidSupplierRFQTransitionError,
        match="at least one supplier",
    ):
        transition_supplier_rfq(
            SupplierRFQStatus.READY,
            SupplierRFQStatus.SENT,
            line_count=1,
            supplier_count=0,
        )


def test_supplier_rfq_rejects_illegal_transition() -> None:
    with pytest.raises(InvalidSupplierRFQTransitionError):
        transition_supplier_rfq(
            SupplierRFQStatus.DRAFT,
            SupplierRFQStatus.AWARDED,
            line_count=1,
            supplier_count=3,
        )


def test_quote_line_requires_unit_price_evidence() -> None:
    with pytest.raises(ValueError, match="unit_price requires source evidence"):
        quote_line(
            relation=IdentityRelation.EXACT,
            quote_evidence=(),
        )


def test_supplier_quote_rejects_line_from_another_quote() -> None:
    line = quote_line(relation=IdentityRelation.EXACT)

    with pytest.raises(
        ValueError,
        match="all supplier quote lines must reference this quote",
    ):
        SupplierQuote(
            id=uuid.UUID("00000000-0000-0000-0000-000000000011"),
            supplier_rfq_id=uuid.UUID("00000000-0000-0000-0000-000000000020"),
            supplier_inquiry_id=uuid.UUID("00000000-0000-0000-0000-000000000021"),
            supplier_id=uuid.UUID("00000000-0000-0000-0000-000000000022"),
            received_at=datetime(2026, 9, 21, tzinfo=timezone.utc),
            currency="EUR",
            status=SupplierQuoteStatus.RECEIVED,
            lines=(line,),
            source_document_ids=(DOCUMENT_ID,),
        )


def test_comparison_cannot_recommend_review_required_candidate() -> None:
    candidate = ComparisonCandidate(
        supplier_quote_line_id=QUOTE_LINE_ID,
        eligibility=Eligibility.REVIEW_REQUIRED,
        rejection_reasons=("IDENTITY_SUBSTITUTE",),
    )

    with pytest.raises(ValueError, match="recommended quote line must be eligible"):
        CommercialComparison(
            id=uuid.UUID("00000000-0000-0000-0000-000000000030"),
            supplier_rfq_line_id=RFQ_LINE_ID,
            comparison_version=1,
            policy_version="rpo-001-v0.1",
            candidates=(candidate,),
            recommended_quote_line_id=QUOTE_LINE_ID,
            created_at=datetime(2026, 9, 21, tzinfo=timezone.utc),
            trace_id=uuid.UUID("00000000-0000-0000-0000-000000000031"),
        )


def test_approved_award_requires_selected_quote() -> None:
    with pytest.raises(
        ValueError,
        match="approved award requires selected_quote_line_id",
    ):
        AwardDecision(
            id=uuid.UUID("00000000-0000-0000-0000-000000000040"),
            supplier_rfq_line_id=RFQ_LINE_ID,
            comparison_id=uuid.UUID("00000000-0000-0000-0000-000000000030"),
            recommended_quote_line_id=QUOTE_LINE_ID,
            outcome=AwardOutcome.APPROVED,
            reason_code=AwardReason.BEST_LANDED_COST,
            policy_version="rpo-001-v0.1",
            decided_by=uuid.UUID("00000000-0000-0000-0000-000000000041"),
            decided_at=datetime(2026, 9, 21, tzinfo=timezone.utc),
            is_override=False,
            trace_id=uuid.UUID("00000000-0000-0000-0000-000000000031"),
        )


def test_award_override_must_match_selected_vs_recommended() -> None:
    selected = uuid.UUID("00000000-0000-0000-0000-000000000201")

    with pytest.raises(
        ValueError,
        match="is_override must reflect recommendation/selection difference",
    ):
        AwardDecision(
            id=uuid.UUID("00000000-0000-0000-0000-000000000042"),
            supplier_rfq_line_id=RFQ_LINE_ID,
            comparison_id=uuid.UUID("00000000-0000-0000-0000-000000000030"),
            recommended_quote_line_id=QUOTE_LINE_ID,
            selected_quote_line_id=selected,
            outcome=AwardOutcome.APPROVED,
            reason_code=AwardReason.MANUAL_OVERRIDE,
            policy_version="rpo-001-v0.1",
            decided_by=uuid.UUID("00000000-0000-0000-0000-000000000041"),
            decided_at=datetime(2026, 9, 21, tzinfo=timezone.utc),
            is_override=False,
            trace_id=uuid.UUID("00000000-0000-0000-0000-000000000031"),
        )


def test_supplier_rfq_cannot_be_ready_without_lines() -> None:
    with pytest.raises(
        InvalidSupplierRFQTransitionError,
        match="at least one line",
    ):
        transition_supplier_rfq(
            SupplierRFQStatus.DRAFT,
            SupplierRFQStatus.READY,
            line_count=0,
            supplier_count=3,
        )
