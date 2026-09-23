from __future__ import annotations

from rfq_cc.domain import (
    CommercialAction,
    CommercialDecision,
    CommitmentLevel,
    CustomerIntent,
    ResponseKind,
)


def decide(intent: CustomerIntent) -> CommercialDecision:
    if intent.response_kind == ResponseKind.APPROVED_FULL:
        if (
            intent.commitment == CommitmentLevel.EXPLICIT_ORDER
            and intent.confidence >= 0.99
        ):
            return CommercialDecision(
                action=CommercialAction.PASS_KT37,
                reason_code="EXPLICIT_CURRENT_QUOTE_APPROVAL",
                requires_human=False,
            )
        return CommercialDecision(
            action=CommercialAction.REVIEW_REQUIRED,
            reason_code="APPROVAL_NOT_EXPLICIT",
        )

    if intent.response_kind == ResponseKind.APPROVED_PARTIAL:
        return CommercialDecision(
            action=CommercialAction.REPRICE,
            reason_code="PARTIAL_QUANTITY_REQUIRES_NEW_QUOTE",
            return_checkpoint="KT33",
        )

    if intent.response_kind == ResponseKind.PRICE_OBJECTION:
        if intent.target_price is None:
            return CommercialDecision(
                action=CommercialAction.REQUEST_TARGET_PRICE,
                reason_code="TARGET_PRICE_UNKNOWN",
            )
        return CommercialDecision(
            action=CommercialAction.REPRICE,
            reason_code="PRICE_CHANGE_REQUIRES_NEW_QUOTE",
            return_checkpoint="KT33",
        )

    if intent.response_kind == ResponseKind.PAYMENT_TERMS_OBJECTION:
        return CommercialDecision(
            action=CommercialAction.CHANGE_PAYMENT_TERMS,
            reason_code="PAYMENT_TERMS_CHANGE",
            return_checkpoint="KT34",
        )

    if intent.response_kind == ResponseKind.PRODUCT_OBJECTION:
        return CommercialDecision(
            action=CommercialAction.PRODUCT_REIDENTIFICATION,
            reason_code="PRODUCT_CHANGE",
            return_checkpoint="KT10",
        )

    if intent.response_kind == ResponseKind.REJECTED:
        return CommercialDecision(
            action=CommercialAction.MARK_LOST,
            reason_code="EXPLICIT_REJECTION",
            requires_human=False,
        )

    if intent.response_kind == ResponseKind.DEFERRED:
        return CommercialDecision(
            action=CommercialAction.FOLLOW_UP,
            reason_code="DEFERRED",
        )

    return CommercialDecision(
        action=CommercialAction.REVIEW_REQUIRED,
        reason_code=f"REVIEW_{intent.response_kind}",
        requires_human=True,
    )
