"""Independent read-only evaluation of RFQ extraction against human labels.

No model calls, catalog access, quote pricing or outbound data transmission.
The ground-truth labels MUST be independently prepared by a qualified reviewer.
"""
from __future__ import annotations

from collections import Counter

from pydantic import Field

from electronics_rfq_agent.verified_extraction.contracts import (
    ExtractionResult,
    StrictModel,
)


class GroundTruthLine(StrictModel):
    source_line_id: str = Field(min_length=1)
    original_text: str = Field(min_length=1)
    part_number_raw: str | None
    quantity_raw: str | None
    unit_raw: str | None


class GroundTruth(StrictModel):
    document_id: str = Field(min_length=1)
    annotation_id: str = Field(min_length=1)
    reviewer_id: str = Field(min_length=1)
    lines: list[GroundTruthLine]


class LineAssessment(StrictModel):
    source_line_id: str
    original_text_match: bool
    part_number_match: bool
    quantity_match: bool
    unit_match: bool


class EvaluationReport(StrictModel):
    document_id: str
    annotation_id: str
    expected_lines: int
    extracted_lines: int
    missing_line_ids: list[str]
    duplicate_line_ids: list[str]
    unexpected_line_ids: list[str]
    line_assessments: list[LineAssessment]
    exact_line_matches: int
    ready_for_human_review: bool


def evaluate_extraction(
    labels: GroundTruth,
    extracted: ExtractionResult,
) -> EvaluationReport:
    """Compare against independent labels, without claiming production accuracy."""
    expected_counts = Counter(line.source_line_id for line in labels.lines)
    actual_counts = Counter(line.source_line_id for line in extracted.lines)
    missing = sorted(
        line_id for line_id, expected in expected_counts.items()
        if actual_counts[line_id] < expected
    )
    duplicates = sorted(
        line_id for line_id, count in actual_counts.items()
        if count > expected_counts[line_id] and line_id in expected_counts
    )
    unexpected = sorted(actual_counts.keys() - expected_counts.keys())

    expected_map = {line.source_line_id: line for line in labels.lines}
    actual_map = {line.source_line_id: line for line in extracted.lines}
    assessments: list[LineAssessment] = []
    for line_id in sorted(expected_map.keys() & actual_map.keys()):
        source = expected_map[line_id]
        result = actual_map[line_id]
        assessments.append(
            LineAssessment(
                source_line_id=line_id,
                original_text_match=source.original_text == result.original_text,
                part_number_match=source.part_number_raw == result.part_number.value,
                quantity_match=source.quantity_raw == result.quantity_raw.value,
                unit_match=source.unit_raw == result.unit_raw.value,
            )
        )

    exact_matches = sum(
        assessment.original_text_match
        and assessment.part_number_match
        and assessment.quantity_match
        and assessment.unit_match
        for assessment in assessments
    )
    complete = (
        labels.document_id == extracted.document_id
        and len(expected_map) == len(labels.lines)
        and len(actual_map) == len(extracted.lines)
        and not missing
        and not duplicates
        and not unexpected
        and exact_matches == len(labels.lines)
    )
    return EvaluationReport(
        document_id=labels.document_id,
        annotation_id=labels.annotation_id,
        expected_lines=len(labels.lines),
        extracted_lines=len(extracted.lines),
        missing_line_ids=missing,
        duplicate_line_ids=duplicates,
        unexpected_line_ids=unexpected,
        line_assessments=assessments,
        exact_line_matches=exact_matches,
        ready_for_human_review=complete,
    )
