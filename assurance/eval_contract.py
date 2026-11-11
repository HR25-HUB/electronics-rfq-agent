"""Synthetic-only RFQ candidate matching reference policy."""
from __future__ import annotations
import json
from pathlib import Path
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field

class Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")

class Candidate(Strict):
    part_number: str
    manufacturer: str | None = None

class Case(Strict):
    id: str
    input_part: str = Field(min_length=1)
    input_manufacturer: str | None = None
    candidates: list[Candidate]
    expected: Literal["matched", "needs_review", "not_found"]

def classify(case: Case) -> str:
    if not case.candidates:
        return "not_found"
    if len(case.candidates) != 1:
        return "needs_review"
    candidate = case.candidates[0]
    if candidate.part_number != case.input_part:
        return "needs_review"
    if case.input_manufacturer is not None and candidate.manufacturer != case.input_manufacturer:
        return "needs_review"
    return "matched"

def evaluate_dataset(path: Path) -> dict[str, object]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    cases = [Case.model_validate(x) for x in raw["cases"]]
    if len({c.id for c in cases}) != len(cases):
        raise ValueError("duplicate test case IDs")
    failed = [c.id for c in cases if classify(c) != c.expected]
    return {"dataset": raw["dataset_id"], "synthetic": True, "total": len(cases),
            "passed": len(cases) - len(failed), "failed": len(failed), "failed_ids": failed}
