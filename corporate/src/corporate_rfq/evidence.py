from __future__ import annotations

import json
from pathlib import Path
from typing import Literal, Protocol

from pydantic import BaseModel, ConfigDict, Field, model_validator

from corporate_rfq.models import (
    DecisionStatus,
    FailureCode,
    ProductIdentityDecision,
    ProductIdentityFailure,
    RawRFQLine,
)


class GoldenCase(BaseModel):
    model_config = ConfigDict(frozen=True)

    case_id: str = Field(min_length=1)
    dataset_version: str = Field(min_length=1)
    source_kind: Literal["synthetic", "real_redacted"]
    rfq_id: str = Field(min_length=1)
    line_id: str = Field(min_length=1)
    raw_text: str = Field(min_length=1)
    expected_kind: Literal["decision", "failure"]
    expected_status: DecisionStatus | None = None
    expected_product_id: str | None = None
    expected_failure_code: FailureCode | None = None
    tags: tuple[str, ...] = ()

    @model_validator(mode="after")
    def validate_expected_outcome(self) -> GoldenCase:
        if self.expected_kind == "decision":
            if self.expected_status is None:
                raise ValueError("decision case requires expected_status")
            if self.expected_failure_code is not None:
                raise ValueError("decision case cannot define expected_failure_code")
            if self.expected_status == DecisionStatus.ACCEPT and self.expected_product_id is None:
                raise ValueError("ACCEPT case requires expected_product_id")
        else:
            if self.expected_failure_code is None:
                raise ValueError("failure case requires expected_failure_code")
            if self.expected_status is not None or self.expected_product_id is not None:
                raise ValueError("failure case cannot define decision expectations")
        return self


class CaseEvaluation(BaseModel):
    model_config = ConfigDict(frozen=True)

    case_id: str
    passed: bool
    unsafe_auto_substitution: bool
    predicted_kind: Literal["decision", "failure"]
    predicted_status: DecisionStatus | None = None
    predicted_product_id: str | None = None
    predicted_failure_code: FailureCode | None = None


class GoldenMetrics(BaseModel):
    model_config = ConfigDict(frozen=True)

    dataset_version: str
    total_cases: int
    passed_cases: int
    case_pass_rate: float
    accepted_count: int
    review_required_count: int
    rejected_count: int
    failure_count: int
    manual_review_rate: float
    exact_match_precision: float | None
    unsafe_auto_substitution_count: int


class ProductIdentityResolver(Protocol):
    def execute(self, raw: RawRFQLine) -> ProductIdentityDecision | ProductIdentityFailure: ...


def load_golden_cases(path: Path) -> tuple[GoldenCase, ...]:
    cases: list[GoldenCase] = []
    seen_ids: set[str] = set()

    for line_number, raw_line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not raw_line.strip():
            continue
        try:
            payload = json.loads(raw_line)
            case = GoldenCase.model_validate(payload)
        except (json.JSONDecodeError, ValueError) as exc:
            raise ValueError(f"Invalid golden case at line {line_number}: {exc}") from exc
        if case.case_id in seen_ids:
            raise ValueError(f"Duplicate golden case_id: {case.case_id}")
        seen_ids.add(case.case_id)
        cases.append(case)

    if not cases:
        raise ValueError("Golden dataset must contain at least one case")

    versions = {case.dataset_version for case in cases}
    if len(versions) != 1:
        raise ValueError(f"Golden dataset must contain exactly one version, got: {sorted(versions)}")

    return tuple(cases)


def _evaluate_case(case: GoldenCase, resolver: ProductIdentityResolver) -> CaseEvaluation:
    result = resolver.execute(
        RawRFQLine(rfq_id=case.rfq_id, line_id=case.line_id, raw_text=case.raw_text)
    )

    if isinstance(result, ProductIdentityDecision):
        passed = (
            case.expected_kind == "decision"
            and result.status == case.expected_status
            and result.canonical_product_id == case.expected_product_id
        )
        unsafe = result.status == DecisionStatus.ACCEPT and (
            case.expected_status != DecisionStatus.ACCEPT
            or result.canonical_product_id != case.expected_product_id
        )
        return CaseEvaluation(
            case_id=case.case_id,
            passed=passed,
            unsafe_auto_substitution=unsafe,
            predicted_kind="decision",
            predicted_status=result.status,
            predicted_product_id=result.canonical_product_id,
        )

    passed = (
        case.expected_kind == "failure" and result.failure_code == case.expected_failure_code
    )
    return CaseEvaluation(
        case_id=case.case_id,
        passed=passed,
        unsafe_auto_substitution=False,
        predicted_kind="failure",
        predicted_failure_code=result.failure_code,
    )


def evaluate_golden_cases(
    cases: tuple[GoldenCase, ...],
    resolver: ProductIdentityResolver,
) -> tuple[GoldenMetrics, tuple[CaseEvaluation, ...]]:
    evaluations = tuple(_evaluate_case(case, resolver) for case in cases)

    accepted_count = sum(
        item.predicted_status == DecisionStatus.ACCEPT for item in evaluations
    )
    review_required_count = sum(
        item.predicted_status == DecisionStatus.REVIEW_REQUIRED for item in evaluations
    )
    rejected_count = sum(
        item.predicted_status == DecisionStatus.REJECT for item in evaluations
    )
    failure_count = sum(item.predicted_kind == "failure" for item in evaluations)
    passed_cases = sum(item.passed for item in evaluations)
    unsafe_count = sum(item.unsafe_auto_substitution for item in evaluations)

    correct_accepts = sum(
        item.predicted_status == DecisionStatus.ACCEPT
        and item.passed
        for item in evaluations
    )
    precision = correct_accepts / accepted_count if accepted_count else None
    total = len(evaluations)

    metrics = GoldenMetrics(
        dataset_version=cases[0].dataset_version,
        total_cases=total,
        passed_cases=passed_cases,
        case_pass_rate=passed_cases / total,
        accepted_count=accepted_count,
        review_required_count=review_required_count,
        rejected_count=rejected_count,
        failure_count=failure_count,
        manual_review_rate=review_required_count / total,
        exact_match_precision=precision,
        unsafe_auto_substitution_count=unsafe_count,
    )
    return metrics, evaluations
