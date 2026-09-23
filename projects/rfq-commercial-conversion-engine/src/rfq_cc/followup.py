from __future__ import annotations

from datetime import datetime, timedelta
from enum import StrEnum

from pydantic import BaseModel


class FollowUpType(StrEnum):
    RECEIPT_CONFIRMATION = "RECEIPT_CONFIRMATION"
    OBJECTION_REVIEW = "OBJECTION_REVIEW"
    RESERVATION_DEADLINE = "RESERVATION_DEADLINE"
    ESCALATION_ALTERNATIVE = "ESCALATION_ALTERNATIVE"


class FollowUp(BaseModel):
    kind: FollowUpType
    due_at: datetime
    objective: str


def build_plan(sent_at: datetime, valid_until: datetime) -> list[FollowUp]:
    return sorted(
        [
            FollowUp(
                kind=FollowUpType.RECEIPT_CONFIRMATION,
                due_at=sent_at + timedelta(minutes=20),
                objective="Confirm receipt/readability",
            ),
            FollowUp(
                kind=FollowUpType.OBJECTION_REVIEW,
                due_at=sent_at + timedelta(hours=24),
                objective="Discover explicit blocker",
            ),
            FollowUp(
                kind=FollowUpType.RESERVATION_DEADLINE,
                due_at=valid_until - timedelta(hours=5),
                objective="Use real reservation/price deadline",
            ),
            FollowUp(
                kind=FollowUpType.ESCALATION_ALTERNATIVE,
                due_at=sent_at + timedelta(days=4),
                objective="Offer phased/alternative fulfillment",
            ),
        ],
        key=lambda x: x.due_at,
    )
