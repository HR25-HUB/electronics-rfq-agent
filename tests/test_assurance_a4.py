"""Synthetic unit tests of A4 contracts, not evidence of real accuracy."""

from __future__ import annotations

from pydantic import ValidationError

from assurance.approval_evidence import ApprovalBundle
from assurance.ground_truth import Case, Dataset, evaluate


def make_cases(count: int = 30) -> list[Case]:
    return [
        Case(
            case_id=f"SYN-{i:04d}",
            source_sha256=f"{i:064x}",
            label_a="matched",
            label_b="matched",
            prediction="matched",
            evidence_ref=f"test-only-{i}",
        )
        for i in range(count)
    ]


def make_dataset(**updates: object) -> Dataset:
    payload = {
        "dataset_id": "unit-test-synthetic",
        "source_kind": "synthetic",
        "consent_record": "test-only",
        "sanitized": True,
        "storage_class": "restricted",
        "primary_annotator": "synthetic-A",
        "secondary_annotator": "synthetic-B",
        "cases": make_cases(),
    }
    payload.update(updates)
    return Dataset.model_validate(payload)


def test_synthetic_never_qualifies_as_real() -> None:
    baseline = evaluate(make_dataset())
    assert baseline.decision == "BLOCK"
    assert baseline.false_accepts == 0


def test_false_accept_blocks() -> None:
    rows = make_cases()
    rows[0] = rows[0].model_copy(
        update={"label_a": "alternative", "label_b": "alternative"}
    )
    baseline = evaluate(make_dataset(cases=rows))
    assert baseline.decision == "BLOCK"
    assert baseline.false_accepts == 1


def test_disagreement_requires_adjudication() -> None:
    rows = make_cases()
    rows[0] = rows[0].model_copy(update={"label_b": "ambiguous"})
    baseline = evaluate(make_dataset(cases=rows))
    assert any("unresolved disagreement" in x for x in baseline.reasons)


def test_duplicate_cases_rejected() -> None:
    rows = make_cases()
    rows.append(rows[0])
    try:
        make_dataset(cases=rows)
    except ValidationError:
        return
    raise AssertionError("duplicate IDs were accepted")


def test_same_annotator_rejected() -> None:
    try:
        make_dataset(secondary_annotator="synthetic-A")
    except ValidationError:
        return
    raise AssertionError("same annotator was accepted")


def test_approval_requires_five_reviewer_attestations() -> None:
    try:
        ApprovalBundle.model_validate({
            "subject_sha": "a" * 40,
            "author": "author",
            "dataset_manifest_sha256": "b" * 64,
            "ci_run_url": "https://github.com/org/repo/actions/runs/1",
            "real_baseline_eligible": False,
            "human_reviewer": "reviewer",
            "human_review_url": "https://github.com/org/repo/pull/1",
            "reviews": [],
        })
    except ValidationError:
        return
    raise AssertionError("missing reviews were accepted")
