from decimal import Decimal

from rfq_cc.domain import (
    CommercialAction,
    CommitmentLevel,
    CustomerIntent,
    ResponseKind,
)
from rfq_cc.policy import decide


def test_conditional_price_commitment_never_passes_kt37() -> None:
    decision = decide(
        CustomerIntent(
            response_kind=ResponseKind.PRICE_OBJECTION,
            commitment=CommitmentLevel.CONDITIONAL,
            confidence=1,
            target_price=Decimal("92"),
        )
    )
    assert decision.action == CommercialAction.REPRICE
    assert decision.return_checkpoint == "KT33"


def test_full_approval_requires_explicit_order() -> None:
    decision = decide(
        CustomerIntent(
            response_kind=ResponseKind.APPROVED_FULL,
            commitment=CommitmentLevel.INTEREST,
            confidence=1,
        )
    )
    assert decision.action == CommercialAction.REVIEW_REQUIRED


def test_explicit_full_approval_can_pass_policy() -> None:
    decision = decide(
        CustomerIntent(
            response_kind=ResponseKind.APPROVED_FULL,
            commitment=CommitmentLevel.EXPLICIT_ORDER,
            confidence=0.99,
            evidence_spans=["Подтверждаем заказ."],
        )
    )
    assert decision.action == CommercialAction.PASS_KT37
