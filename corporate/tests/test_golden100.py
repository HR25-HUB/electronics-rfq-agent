# ruff: noqa: I001
from collections import Counter
from pathlib import Path

from corporate_rfq.evidence import evaluate_golden_cases, load_golden_cases
from corporate_rfq.service import FakeCatalog, ResolveProductIdentity


GOLDEN100 = Path(__file__).parent / "golden" / "golden100-adversarial.jsonl"


def test_golden100_contract_and_distribution() -> None:
    cases = load_golden_cases(GOLDEN100)

    assert len(cases) == 100
    assert {case.dataset_version for case in cases} == {"synthetic-adversarial-v1.0"}
    assert {case.source_kind for case in cases} == {"synthetic"}

    expected = Counter(
        "FAILURE" if case.expected_kind == "failure" else case.expected_status.value
        for case in cases
    )
    assert expected == {
        "ACCEPT": 15,
        "REVIEW_REQUIRED": 50,
        "REJECT": 20,
        "FAILURE": 15,
    }

    strata = Counter(case.tags[0] for case in cases)
    assert strata == {
        "A_exact_valid": 15,
        "B_missing_manufacturer": 15,
        "C_mpn_noise": 20,
        "D_critical_conflict": 20,
        "E_quantity_ambiguity": 15,
        "F_semantic_or_analogue": 15,
    }


def test_golden100_has_no_unsafe_auto_substitution() -> None:
    cases = load_golden_cases(GOLDEN100)
    metrics, _ = evaluate_golden_cases(
        cases,
        ResolveProductIdentity(FakeCatalog()),
    )

    assert metrics.total_cases == 100
    assert metrics.unsafe_auto_substitution_count == 0
