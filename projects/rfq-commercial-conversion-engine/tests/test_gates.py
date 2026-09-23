from datetime import datetime, timezone
from decimal import Decimal

from rfq_cc.domain import (
    CustomerDecisionEvidence,
    OrderReference,
    QuoteReference,
    ResponseKind,
)
from rfq_cc.gates import validate_kt37, validate_kt38


def quote() -> QuoteReference:
    return QuoteReference(
        line_id="L",
        quote_id="Q",
        quote_version=4,
        quantity=Decimal("50"),
        unit_price=Decimal("92"),
        currency="EUR",
    )


def test_kt37_blocks_old_quote_version() -> None:
    evidence = CustomerDecisionEvidence(
        decision_id="D",
        line_id="L",
        quote_id="Q",
        quote_version=3,
        interaction_id="I",
        response_kind=ResponseKind.APPROVED_FULL,
        evidence_text="Подтверждаем.",
        decided_at=datetime.now(timezone.utc),
    )
    assert validate_kt37(quote=quote(), evidence=evidence).passed is False


def test_kt38_exact_match_passes() -> None:
    order = OrderReference(
        line_id="L",
        order_id="O",
        source_quote_version=4,
        quantity=Decimal("50"),
        unit_price=Decimal("92"),
        currency="EUR",
    )
    assert validate_kt38(quote=quote(), order=order).passed is True


def test_kt38_price_mismatch_blocks() -> None:
    order = OrderReference(
        line_id="L",
        order_id="O",
        source_quote_version=4,
        quantity=Decimal("50"),
        unit_price=Decimal("91"),
        currency="EUR",
    )
    assert validate_kt38(quote=quote(), order=order).reason_code == "PRICE_MISMATCH"
