"""Fail-closed, privacy-minimizing validation of expert ground truth.

This module consumes an externally curated, consented dataset manifest.
No production RFQ content or supplier pricing belongs in this repository.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

Label = Literal["matched", "alternative", "ambiguous", "missing", "erp_error"]
SHA256_PATTERN = r"^[a-f0-9]{64}$"


class Strict(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class Case(Strict):
    case_id: str = Field(min_length=4)
    source_sha256: str = Field(pattern=SHA256_PATTERN)
    label_a: Label
    label_b: Label
    adjudicated_label: Label | None = None
    prediction: Label
    evidence_ref: str = Field(min_length=4)


class Dataset(Strict):
    dataset_id: str = Field(min_length=5)
    source_kind: Literal["real", "synthetic"]
    consent_record: str = Field(min_length=4)
    sanitized: bool
    storage_class: Literal["restricted", "approved_internal"]
    primary_annotator: str = Field(min_length=2)
    secondary_annotator: str = Field(min_length=2)
    adjudicator: str | None = None
    cases: list[Case] = Field(min_length=1)

    @model_validator(mode="after")
    def distinct_annotators(self) -> Dataset:
        if self.primary_annotator == self.secondary_annotator:
            raise ValueError("independent annotators required")
        ids = [item.case_id for item in self.cases]
        if len(ids) != len(set(ids)):
            raise ValueError("duplicate case IDs")
        return self


class Baseline(Strict):
    dataset_id: str
    cases: int
    disagreements: int
    false_accepts: int
    predicted_accepts: int
    label_accuracy: float
    false_accept_rate: float | None
    decision: Literal["BLOCK", "ELIGIBLE_FOR_EXPERT_REVIEW"]
    reasons: list[str]


def evaluate(dataset: Dataset, *, minimum_cases: int = 30) -> Baseline:
    """Evaluate exact label equality; conservative automatic acceptance only.

    Prediction 'matched' is the sole automatic acceptance class. Every other
    prediction requires intervention. This is a baseline contract, not a model
    inference or a proof of data provenance.
    """
    reasons: list[str] = []
    if dataset.source_kind != "real":
        reasons.append("synthetic dataset cannot qualify as real baseline")
    if not dataset.sanitized:
        reasons.append("sanitization not attested")
    if len(dataset.cases) < minimum_cases:
        reasons.append(f"sample count below {minimum_cases}")
    if not dataset.consent_record:
        reasons.append("consent evidence missing")
    disagreements = 0
    resolved: list[Label] = []
    for case in dataset.cases:
        if case.label_a != case.label_b:
            disagreements += 1
            if case.adjudicated_label is None or not dataset.adjudicator:
                reasons.append(f"unresolved disagreement: {case.case_id}")
        if case.adjudicated_label is not None:
            resolved.append(case.adjudicated_label)
        else:
            resolved.append(case.label_a)
    accepts = sum(item.prediction == "matched" for item in dataset.cases)
    false_accepts = sum(
        item.prediction == "matched" and truth != "matched"
        for item, truth in zip(dataset.cases, resolved, strict=True)
    )
    accurate = sum(
        item.prediction == truth
        for item, truth in zip(dataset.cases, resolved, strict=True)
    )
    if false_accepts:
        reasons.append("false positive automatic matches detected")
    if accepts == 0:
        reasons.append("no accepted matches: false-accept rate undefined")
    return Baseline(
        dataset_id=dataset.dataset_id,
        cases=len(dataset.cases),
        disagreements=disagreements,
        false_accepts=false_accepts,
        predicted_accepts=accepts,
        label_accuracy=accurate / len(dataset.cases),
        false_accept_rate=false_accepts / accepts if accepts else None,
        decision="BLOCK" if reasons else "ELIGIBLE_FOR_EXPERT_REVIEW",
        reasons=sorted(set(reasons)),
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("manifest", type=Path)
    args = parser.parse_args()
    try:
        dataset = Dataset.model_validate_json(args.manifest.read_text(encoding="utf-8"))
        result = evaluate(dataset)
        print(result.model_dump_json(indent=2))
        return int(result.decision == "BLOCK")
    except (OSError, ValueError) as exc:
        print(json.dumps({"decision": "BLOCK", "error": str(exc)}))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
