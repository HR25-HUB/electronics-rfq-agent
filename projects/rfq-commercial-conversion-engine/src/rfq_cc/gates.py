from __future__ import annotations

from rfq_cc.domain import (
    CustomerDecisionEvidence,
    GateResult,
    OrderReference,
    QuoteReference,
    ResponseKind,
)


def validate_kt37(
    *, quote: QuoteReference, evidence: CustomerDecisionEvidence
) -> GateResult:
    if evidence.line_id != quote.line_id:
        return GateResult(passed=False, reason_code="LINE_MISMATCH")
    if (
        evidence.quote_id != quote.quote_id
        or evidence.quote_version != quote.quote_version
    ):
        return GateResult(passed=False, reason_code="QUOTE_VERSION_MISMATCH")
    if evidence.response_kind != ResponseKind.APPROVED_FULL:
        return GateResult(passed=False, reason_code="NOT_FULL_APPROVAL")
    if not evidence.evidence_text.strip():
        return GateResult(passed=False, reason_code="EVIDENCE_MISSING")
    return GateResult(passed=True, reason_code="KT37_PASS")


def validate_kt38(*, quote: QuoteReference, order: OrderReference) -> GateResult:
    if order.line_id != quote.line_id:
        return GateResult(passed=False, reason_code="LINE_MISMATCH")
    if order.source_quote_version != quote.quote_version:
        return GateResult(passed=False, reason_code="QUOTE_VERSION_MISMATCH")
    if order.quantity != quote.quantity:
        return GateResult(passed=False, reason_code="QUANTITY_MISMATCH")
    if order.unit_price != quote.unit_price:
        return GateResult(passed=False, reason_code="PRICE_MISMATCH")
    if order.currency != quote.currency:
        return GateResult(passed=False, reason_code="CURRENCY_MISMATCH")
    return GateResult(passed=True, reason_code="KT38_PASS")
