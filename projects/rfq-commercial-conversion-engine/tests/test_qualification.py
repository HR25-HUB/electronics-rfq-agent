from rfq_cc.domain import (
    NeedContext,
    PrimaryCriterion,
    QualificationClass,
    QualificationInput,
)
from rfq_cc.qualification import qualify, resource_budget


def test_price_monitoring_uses_low_cost_path() -> None:
    snapshot = qualify(
        QualificationInput(
            line_id="L",
            deal_id="D",
            need_context=NeedContext.PRICE_MONITORING,
            primary_criterion=PrimaryCriterion.LOWEST_UNIT_PRICE,
        )
    )
    assert snapshot.classification == QualificationClass.COLD_CALCULATION
    assert resource_budget(snapshot.classification).max_manual_minutes == 8


def test_well_qualified_project_is_hot() -> None:
    snapshot = qualify(
        QualificationInput(
            line_id="L",
            deal_id="D",
            need_context=NeedContext.PROJECT,
            primary_criterion=PrimaryCriterion.DELIVERY_DEADLINE,
            decision_deadline_known=True,
            decision_maker_known=True,
            budget_process_known=True,
            competitors_known=True,
            explicit_project_or_need=True,
            customer_engaged_in_dialogue=True,
            agreed_success_condition=True,
        )
    )
    assert snapshot.classification == QualificationClass.HOT
