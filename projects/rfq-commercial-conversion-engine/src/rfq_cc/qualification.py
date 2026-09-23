from __future__ import annotations

from rfq_cc.domain import (
    NeedContext,
    PrimaryCriterion,
    QualificationClass,
    QualificationInput,
    QualificationSnapshot,
    ResourceBudget,
)


def qualify(x: QualificationInput) -> QualificationSnapshot:
    score = 0
    missing: list[str] = []

    if x.explicit_project_or_need:
        score += 25
    else:
        missing.append("explicit_project_or_need")

    if x.need_context != NeedContext.UNKNOWN:
        score += 10
    else:
        missing.append("need_context")

    if x.decision_deadline_known:
        score += 15
    else:
        missing.append("decision_deadline")

    if x.decision_maker_known:
        score += 10
    else:
        missing.append("decision_maker")

    if x.budget_process_known:
        score += 10
    else:
        missing.append("budget_process")

    if x.competitors_known:
        score += 5

    if x.primary_criterion != PrimaryCriterion.UNKNOWN:
        score += 10
    else:
        missing.append("primary_criterion")

    if x.agreed_success_condition:
        score += 10
    else:
        missing.append("agreed_success_condition")

    if x.customer_engaged_in_dialogue:
        score += 5

    if x.need_context == NeedContext.PRICE_MONITORING or not x.customer_engaged_in_dialogue:
        classification = QualificationClass.COLD_CALCULATION
    elif score >= 75:
        classification = QualificationClass.HOT
    elif score >= 50:
        classification = QualificationClass.WARM
    else:
        classification = QualificationClass.REVIEW_REQUIRED

    return QualificationSnapshot(
        **x.model_dump(),
        score=score,
        classification=classification,
        missing_fields=missing,
    )


def resource_budget(cls: QualificationClass) -> ResourceBudget:
    mapping = {
        QualificationClass.HOT: ResourceBudget(
            max_manual_minutes=45,
            supplier_target_count=8,
            expert_review_allowed=True,
            mandatory_presentation=True,
        ),
        QualificationClass.WARM: ResourceBudget(
            max_manual_minutes=25,
            supplier_target_count=5,
            expert_review_allowed=True,
            mandatory_presentation=True,
        ),
        QualificationClass.COLD_CALCULATION: ResourceBudget(
            max_manual_minutes=8,
            supplier_target_count=3,
            expert_review_allowed=False,
            mandatory_presentation=False,
        ),
        QualificationClass.REVIEW_REQUIRED: ResourceBudget(
            max_manual_minutes=15,
            supplier_target_count=3,
            expert_review_allowed=False,
            mandatory_presentation=False,
        ),
    }
    return mapping[cls]


def next_best_question(snapshot: QualificationSnapshot) -> str | None:
    bank = {
        "explicit_project_or_need": (
            "Это закупка под текущий проект, пополнение склада или перепродажа?"
        ),
        "decision_deadline": "К какой дате нужно принять решение и получить товар?",
        "decision_maker": "Кто ещё участвует в утверждении закупки?",
        "budget_process": "Бюджет уже утверждён или ещё требует согласования?",
        "primary_criterion": (
            "Что важнее: цена, комплектация, срок поставки или условия оплаты?"
        ),
        "agreed_success_condition": (
            "Если выполним ключевые условия, готовы разместить заказ в согласованный срок?"
        ),
    }
    priority = (
        "explicit_project_or_need",
        "decision_deadline",
        "decision_maker",
        "budget_process",
        "primary_criterion",
        "agreed_success_condition",
    )
    for key in priority:
        if key in snapshot.missing_fields:
            return bank[key]
    return None
