import json
from pathlib import Path

from rfq_cc.domain import CommitmentLevel, CustomerIntent, ResponseKind
from rfq_cc.policy import decide


def test_golden_cases_follow_expected_policy() -> None:
    path = Path(__file__).parents[1] / "evidence" / "synthetic" / "golden_cases.json"
    cases = json.loads(path.read_text(encoding="utf-8"))

    for case in cases:
        intent = CustomerIntent(
            response_kind=ResponseKind(case["response_kind"]),
            commitment=CommitmentLevel(case["commitment"]),
            confidence=1.0,
            target_price=case.get("target_price"),
            evidence_spans=[case["customer_text"]],
        )
        decision = decide(intent)
        assert decision.action.value == case["expected_action"]
        if "expected_return" in case:
            assert decision.return_checkpoint == case["expected_return"]
