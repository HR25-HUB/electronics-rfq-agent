from __future__ import annotations

import argparse
import json
from decimal import Decimal

from rfq_cc.domain import (
    CommitmentLevel,
    CustomerIntent,
    NeedContext,
    PrimaryCriterion,
    QualificationInput,
    ResponseKind,
)
from rfq_cc.policy import decide
from rfq_cc.qualification import qualify, resource_budget


def demo() -> None:
    snapshot = qualify(
        QualificationInput(
            line_id="L-001",
            deal_id="D-001",
            need_context=NeedContext.PROJECT,
            primary_criterion=PrimaryCriterion.DELIVERY_DEADLINE,
            decision_deadline_known=True,
            decision_maker_known=True,
            budget_process_known=True,
            explicit_project_or_need=True,
            customer_engaged_in_dialogue=True,
            agreed_success_condition=True,
        )
    )

    intent = CustomerIntent(
        response_kind=ResponseKind.PRICE_OBJECTION,
        commitment=CommitmentLevel.CONDITIONAL,
        confidence=1.0,
        target_price=Decimal("92"),
        evidence_spans=["Если будет 92 EUR, готовы заказать."],
    )

    print(
        json.dumps(
            {
                "qualification": snapshot.model_dump(mode="json"),
                "resource_budget": resource_budget(snapshot.classification).model_dump(
                    mode="json"
                ),
                "decision": decide(intent).model_dump(mode="json"),
            },
            ensure_ascii=False,
            indent=2,
        )
    )


def main() -> None:
    parser = argparse.ArgumentParser(prog="rfq-cc")
    parser.add_argument("command", choices=["demo"])
    args = parser.parse_args()
    if args.command == "demo":
        demo()


if __name__ == "__main__":
    main()
