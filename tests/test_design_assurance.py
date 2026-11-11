"""Isolated fail-closed assurance and 20 synthetic matching scenarios."""

from pathlib import Path

from assurance.eval_contract import evaluate_dataset
from assurance.review_contract import Evaluation, Evidence, Perspective, Review
from assurance.review_gate import evaluate

ROOT = Path(__file__).resolve().parents[1]


def _evidence() -> Evidence:
    return Evidence(
        change_id="NUIF-SDD-ASSURANCE-001.A2",
        commit_sha="a" * 40,
        designer="elephant",
        requirements={"RFQ-MATCH-001": ["tests/test_design_assurance.py"]},
        reviews=[],
        checks={},
        evaluation=Evaluation(
            dataset="synthetic",
            total=20,
            passed=20,
            failed=0,
            synthetic=True,
        ),
    )


def test_synthetic_20() -> None:
    report = evaluate_dataset(ROOT / "evals/nuif_assurance_synthetic.json")
    assert report["total"] == 20
    assert report["failed"] == 0


def test_missing_reviews_fails_closed() -> None:
    errors = evaluate(_evidence(), ROOT, "a" * 40)
    assert any("missing/duplicate review" in error for error in errors)
    assert "human approval missing" in errors
    assert "synthetic eval is not production evidence" in errors


def test_self_review_is_rejected() -> None:
    review = Review(
        perspective=Perspective.TECHNICAL,
        reviewer="elephant",
        session_id="separate-123",
        independent_context=True,
        artifact_sha256={"README.md": "0" * 64},
        completed=True,
    )
    record = _evidence().model_copy(update={"reviews": [review]})
    assert "review independence not established" in evaluate(record, ROOT, "a" * 40)
