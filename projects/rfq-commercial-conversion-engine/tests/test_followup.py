from datetime import datetime, timedelta, timezone

from rfq_cc.followup import FollowUpType, build_plan


def test_followup_has_four_controlled_actions() -> None:
    sent = datetime(2026, 9, 23, 10, tzinfo=timezone.utc)
    plan = build_plan(sent, sent + timedelta(days=2))
    assert len(plan) == 4
    assert plan[0].kind == FollowUpType.RECEIPT_CONFIRMATION
