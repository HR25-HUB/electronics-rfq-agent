"""Synthetic-only acceptance tests for independent RFQ line evaluation."""
from __future__ import annotations

from electronics_rfq_agent.verified_extraction.contracts import (
    ExtractedField,
    ExtractedLine,
    ExtractionResult,
)
from electronics_rfq_agent.verified_extraction.evaluation import (
    GroundTruth,
    GroundTruthLine,
    evaluate_extraction,
)


def fixtures() -> tuple[GroundTruth, ExtractionResult]:
    labels = GroundTruth(
        document_id="SYNTH-D1",
        annotation_id="ANNO-SYNTH-001",
        reviewer_id="qualified-synthetic-reviewer",
        lines=[
            GroundTruthLine(
                source_line_id="L1",
                original_text="ABB S203-C16 — 100 pcs",
                part_number_raw="S203-C16",
                quantity_raw="100",
                unit_raw="pcs",
            ),
            GroundTruthLine(
                source_line_id="L2",
                original_text="Schneider LC1D09 — 20 pcs",
                part_number_raw="LC1D09",
                quantity_raw="20",
                unit_raw="pcs",
            ),
        ],
    )
    result = ExtractionResult(
        document_id="SYNTH-D1",
        lines=[
            ExtractedLine(
                source_line_id=line.source_line_id,
                original_text=line.original_text,
                part_number=ExtractedField(value=line.part_number_raw),
                quantity_raw=ExtractedField(value=line.quantity_raw),
                unit_raw=ExtractedField(value=line.unit_raw),
            )
            for line in labels.lines
        ],
    )
    return labels, result


def test_exact_ground_truth_passes_review_eligibility() -> None:
    labels, result = fixtures()
    report = evaluate_extraction(labels, result)
    assert report.ready_for_human_review
    assert report.exact_line_matches == 2
    assert report.missing_line_ids == []


def test_missing_line_detected() -> None:
    labels, result = fixtures()
    changed = result.model_copy(update={"lines": result.lines[:1]})
    report = evaluate_extraction(labels, changed)
    assert not report.ready_for_human_review
    assert report.missing_line_ids == ["L2"]


def test_duplicate_line_detected() -> None:
    labels, result = fixtures()
    changed = result.model_copy(
        update={"lines": [*result.lines, result.lines[0]]}
    )
    report = evaluate_extraction(labels, changed)
    assert not report.ready_for_human_review
    assert report.duplicate_line_ids == ["L1"]


def test_wrong_quantity_detected() -> None:
    labels, result = fixtures()
    line = result.lines[0]
    quantity = line.quantity_raw.model_copy(update={"value": "1000"})
    changed = result.model_copy(
        update={
            "lines": [
                line.model_copy(update={"quantity_raw": quantity}),
                result.lines[1],
            ]
        }
    )
    report = evaluate_extraction(labels, changed)
    assert not report.ready_for_human_review
    assert report.line_assessments[0].quantity_match is False


def test_unexpected_line_detected() -> None:
    labels, result = fixtures()
    additional = result.lines[0].model_copy(
        update={"source_line_id": "L99"}
    )
    changed = result.model_copy(
        update={"lines": [*result.lines, additional]}
    )
    report = evaluate_extraction(labels, changed)
    assert not report.ready_for_human_review
    assert report.unexpected_line_ids == ["L99"]


def test_wrong_document_id_rejected() -> None:
    labels, result = fixtures()
    changed = result.model_copy(update={"document_id": "OTHER"})
    report = evaluate_extraction(labels, changed)
    assert not report.ready_for_human_review


def test_incorrect_original_text_detected() -> None:
    labels, result = fixtures()
    wrong = result.lines[0].model_copy(
        update={"original_text": "altered source"}
    )
    changed = result.model_copy(
        update={"lines": [wrong, result.lines[1]]}
    )
    report = evaluate_extraction(labels, changed)
    assert not report.ready_for_human_review
    assert report.line_assessments[0].original_text_match is False


def test_empty_ground_truth_cannot_approve() -> None:
    labels, result = fixtures()
    empty_labels = labels.model_copy(update={"lines": []})
    empty_result = result.model_copy(update={"lines": []})
    report = evaluate_extraction(empty_labels, empty_result)
    assert not report.ready_for_human_review


def test_duplicate_human_labels_are_not_automatically_accepted() -> None:
    labels, result = fixtures()
    duplicate = labels.model_copy(
        update={"lines": [*labels.lines, labels.lines[0]]}
    )
    report = evaluate_extraction(duplicate, result)
    assert not report.ready_for_human_review
