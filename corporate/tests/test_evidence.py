from __future__ import annotations

from pathlib import Path

from corporate_rfq.evidence import GoldenCase, evaluate_golden_cases, load_golden_cases
from corporate_rfq.models import (
    DecisionStatus,
    MatchRelation,
    ProductIdentityDecision,
    RawRFQLine,
)
from corporate_rfq.service import FakeCatalog, ResolveProductIdentity


SEED = Path(__file__).parent / "golden" / "seed.jsonl"


def test_seed_dataset_is_versioned_and_valid() -> None:
    cases = load_golden_cases(SEED)

    assert len(cases) == 10
    assert {case.dataset_version for case in cases} == {"synthetic-seed-v0.1"}
    assert {case.source_kind for case in cases} == {"synthetic"}


def test_seed_dataset_has_zero_unsafe_auto_substitutions() -> None:
    cases = load_golden_cases(SEED)
    metrics, evaluations = evaluate_golden_cases(
        cases,
        ResolveProductIdentity(FakeCatalog()),
    )

    assert metrics.total_cases == 10
    assert metrics.passed_cases == 10
    assert metrics.case_pass_rate == 1.0
    assert metrics.accepted_count == 3
    assert metrics.review_required_count == 3
    assert metrics.rejected_count == 3
    assert metrics.failure_count == 1
    assert metrics.manual_review_rate == 0.3
    assert metrics.exact_match_precision == 1.0
    assert metrics.unsafe_auto_substitution_count == 0
    assert all(item.passed for item in evaluations)


class UnsafeResolver:
    def execute(self, raw: RawRFQLine) -> ProductIdentityDecision:
        return ProductIdentityDecision(
            rfq_id=raw.rfq_id,
            line_id=raw.line_id,
            status=DecisionStatus.ACCEPT,
            relation=MatchRelation.POSSIBLE_MATCH,
            canonical_product_id="WRONG:SKU",
            confidence=0.99,
            policy_reasons=("intentionally unsafe test resolver",),
        )


def test_evaluator_detects_unsafe_auto_substitution() -> None:
    case = GoldenCase(
        case_id="unsafe-001",
        dataset_version="unsafe-test-v1",
        source_kind="synthetic",
        rfq_id="RFQ-X",
        line_id="1",
        raw_text="ABB автомат трехполюсный 16А — 5 шт",
        expected_kind="decision",
        expected_status=DecisionStatus.REVIEW_REQUIRED,
        expected_product_id=None,
    )

    metrics, evaluations = evaluate_golden_cases((case,), UnsafeResolver())

    assert metrics.unsafe_auto_substitution_count == 1
    assert metrics.case_pass_rate == 0.0
    assert evaluations[0].unsafe_auto_substitution is True
