"""Fail-closed, read-only verification of RFQ extraction evidence.

This module intentionally does not alter the legacy RFQParser or QuoteAgent.
"""
from __future__ import annotations

from collections import Counter
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, model_validator


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class EvidenceBlock(StrictModel):
    evidence_id: str = Field(min_length=1)
    page: int = Field(ge=1)
    text: str = Field(min_length=1)


class SourceLine(StrictModel):
    source_line_id: str = Field(min_length=1)
    evidence_id: str = Field(min_length=1)
    original_text: str = Field(min_length=1)


class SourceSpan(StrictModel):
    evidence_id: str = Field(min_length=1)
    start: int = Field(ge=0)
    end: int = Field(gt=0)


class ExtractedField(StrictModel):
    value: str | None
    span: SourceSpan | None = None


class ExtractedLine(StrictModel):
    source_line_id: str
    original_text: str
    part_number: ExtractedField
    quantity_raw: ExtractedField
    unit_raw: ExtractedField


class ExtractionResult(StrictModel):
    document_id: str = Field(min_length=1)
    lines: list[ExtractedLine]
    unknowns: list[str] = Field(default_factory=list)


class EvidenceBundle(StrictModel):
    document_id: str = Field(min_length=1)
    authorization_id: str = Field(min_length=1)
    synthetic: bool
    evidence: list[EvidenceBlock]
    source_lines: list[SourceLine]


class GateStatus(str, Enum):
    BLOCKED = "blocked"
    REVIEW_REQUIRED = "review_required"
    VERIFIED = "verified"


class VerificationReport(StrictModel):
    document_id: str
    result_sha256: str
    errors: list[str]
    coverage_verified: bool
    approval_result_sha256: str | None = None
    status: GateStatus

    @model_validator(mode="after")
    def enforce_gate(self) -> VerificationReport:
        expected = GateStatus.BLOCKED if self.errors else (
            GateStatus.VERIFIED if self.coverage_verified
            and self.approval_result_sha256 == self.result_sha256
            else GateStatus.REVIEW_REQUIRED
        )
        if self.status != expected:
            raise ValueError(f"Invalid release status: expected {expected}")
        return self


def verify(
    bundle: EvidenceBundle,
    result: ExtractionResult,
    *,
    result_sha256: str,
    approval_result_sha256: str | None = None,
) -> VerificationReport:
    """Validate provenance, row coverage, and approval-bound result identity."""
    errors: list[str] = []
    blocks = {b.evidence_id: b for b in bundle.evidence}
    source = {s.source_line_id: s for s in bundle.source_lines}
    if len(blocks) != len(bundle.evidence):
        errors.append("duplicate_evidence_id")
    if len(source) != len(bundle.source_lines):
        errors.append("duplicate_source_line_id")
    if bundle.document_id != result.document_id:
        errors.append("document_id_mismatch")
    for line in bundle.source_lines:
        block = blocks.get(line.evidence_id)
        if block is None or line.original_text not in block.text:
            errors.append(f"invalid_source_line:{line.source_line_id}")

    expected = Counter(x.source_line_id for x in bundle.source_lines)
    actual = Counter(x.source_line_id for x in result.lines)
    for key in sorted(expected.keys() - actual.keys()):
        errors.append(f"missing_line:{key}")
    for key in sorted(actual.keys() - expected.keys()):
        errors.append(f"unknown_line:{key}")
    for key in sorted(k for k, v in actual.items() if v > 1):
        errors.append(f"duplicate_line:{key}")

    for line in result.lines:
        src = source.get(line.source_line_id)
        if src is None:
            continue
        if line.original_text != src.original_text:
            errors.append(f"original_mismatch:{line.source_line_id}")
        block = blocks.get(src.evidence_id)
        for field_name in ("part_number", "quantity_raw", "unit_raw"):
            field = getattr(line, field_name)
            prefix = f"{line.source_line_id}:{field_name}"
            if field.value is None:
                if field.span is not None:
                    errors.append(f"unknown_has_span:{prefix}")
                continue
            if field.span is None:
                errors.append(f"missing_span:{prefix}")
                continue
            span = field.span
            if span.evidence_id != src.evidence_id or block is None:
                errors.append(f"wrong_evidence:{prefix}")
            elif not 0 <= span.start < span.end <= len(block.text):
                errors.append(f"invalid_span:{prefix}")
            elif block.text[span.start:span.end] != field.value:
                errors.append(f"source_mismatch:{prefix}")

    errors = sorted(set(errors))
    coverage_verified = not any(
        e.startswith(("missing_line:", "unknown_line:", "duplicate_line:", "duplicate_source_line_id", "invalid_source_line:"))
        for e in errors
    )
    status = GateStatus.BLOCKED if errors else (
        GateStatus.VERIFIED if coverage_verified and
        approval_result_sha256 == result_sha256 else GateStatus.REVIEW_REQUIRED
    )
    return VerificationReport(
        document_id=bundle.document_id,
        result_sha256=result_sha256,
        errors=errors,
        coverage_verified=coverage_verified,
        approval_result_sha256=approval_result_sha256,
        status=status,
    )
