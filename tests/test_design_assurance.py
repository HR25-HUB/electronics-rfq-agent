"""Isolated fail-closed assurance and 20 synthetic matching scenarios."""
from pathlib import Path
from assurance.eval_contract import evaluate_dataset
from assurance.review_contract import Evidence, Evaluation, Perspective, Review
from assurance.review_gate import evaluate

ROOT = Path(__file__).resolve().parents[1]

def test_synthetic_20():
    report = evaluate_dataset(ROOT / "evals/nuif_assurance_synthetic.json")
    assert report["total"] == 20
    assert report["failed"] == 0

def test_missing_reviews_fails_closed():
    record = Evidence(
        change_id="NUIF-SDD-ASSURANCE-001.A2",
        commit_sha="a" * 40, designer="elephant",
        requirements={"RFQ-MATCH-001": ["tests/test_design_assurance.py"]},
        reviews=[], checks={}, evaluation=Evaluation(
            dataset="synthetic", total=20, passed=20, failed=0, synthetic=True
        ),
    )
    errors = evaluate(record, ROOT, "a" * 40)
    assert any("missing/duplicate review" in x for x in errors)
    assert "human approval missing" in errors
    assert "synthetic eval is not production evidence" in errors

def test_self_review_is_rejected():
    record = Evidence(
        change_id="A2", commit_sha="a" * 40, designer="elephant",
        requirements={"R": ["tests/test_design_assurance.py"]},
        reviews=[Review(
            perspective=Perspective.TECHNICAL,
            reviewer="elephant", session_id="separate-123",
            independent_context=True, artifact_sha256={"README.md": "0" * 64},
            completed=True
        )],
        checks={}, evaluation=Evaluation(
            dataset="synthetic", total=1, passed=1, failed=0, synthetic=True
        )
    )
    assert "review independence not established" in evaluate(record, ROOT, "a" * 40)
