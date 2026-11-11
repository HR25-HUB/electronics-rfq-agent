"""Pydantic v2 evidence and independent design review contracts."""
from __future__ import annotations
from enum import Enum
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, model_validator

class Strict(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

class Perspective(str, Enum):
    PROBLEM = "problem_validity"
    COMPREHENSION = "comprehension"
    TECHNICAL = "technical_critique"
    COMPLEXITY = "complexity_control"
    READINESS = "implementation_readiness"

class Finding(Strict):
    id: str = Field(pattern=r"^DR-[0-9]{3,}$")
    perspective: Perspective
    severity: Literal["blocker", "major", "minor"]
    claim: str = Field(min_length=12)
    evidence: list[str] = Field(min_length=1)
    disposition: Literal["open", "fixed", "risk_accepted", "rejected"] = "open"
    reason: str | None = None
    approved_by: str | None = None

    @model_validator(mode="after")
    def validate_decision(self) -> "Finding":
        if self.disposition != "open" and not self.reason:
            raise ValueError("decision reason required")
        if self.disposition in ("risk_accepted", "rejected") and not self.approved_by:
            raise ValueError("explicit approver required")
        return self

class Review(Strict):
    perspective: Perspective
    reviewer: str = Field(min_length=2)
    session_id: str = Field(min_length=4)
    independent_context: bool
    artifact_sha256: dict[str, str] = Field(min_length=1)
    findings: list[Finding] = Field(default_factory=list)
    completed: bool = False

class Evaluation(Strict):
    dataset: str
    total: int = Field(gt=0)
    passed: int = Field(ge=0)
    failed: int = Field(ge=0)
    synthetic: bool

    @model_validator(mode="after")
    def counts(self) -> "Evaluation":
        if self.passed + self.failed != self.total:
            raise ValueError("invalid evaluation counts")
        return self

class Evidence(Strict):
    change_id: str
    commit_sha: str = Field(pattern=r"^[0-9a-f]{40}$")
    designer: str
    requirements: dict[str, list[str]] = Field(min_length=1)
    reviews: list[Review]
    checks: dict[str, bool]
    evaluation: Evaluation
    human_approved: bool = False
    human_approver: str | None = None

    @model_validator(mode="after")
    def human(self) -> "Evidence":
        if self.human_approved and not self.human_approver:
            raise ValueError("human approver required")
        return self
