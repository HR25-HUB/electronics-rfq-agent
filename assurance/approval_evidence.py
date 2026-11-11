"""Validate external, SHA-bound independent review and approval metadata.

External review URLs must additionally be authenticated using GitHub API.
No self-issued assertion in this file is sufficient for merging a PR.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

SHA = r"^[0-9a-f]{40}$"


class Strict(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class ReviewAttestation(Strict):
    perspective: Literal[
        "problem_validity",
        "comprehension",
        "technical_critique",
        "complexity_control",
        "implementation_readiness",
    ]
    reviewer: str = Field(min_length=2)
    session_id: str = Field(min_length=4)
    review_url: str = Field(pattern=r"^https://github[.]com/")
    commit_sha: str = Field(pattern=SHA)
    conclusion: Literal["approve", "request_changes"]


class ApprovalBundle(Strict):
    subject_sha: str = Field(pattern=SHA)
    author: str = Field(min_length=2)
    dataset_manifest_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    ci_run_url: str = Field(pattern=r"^https://github[.]com/")
    real_baseline_eligible: bool
    human_reviewer: str = Field(min_length=2)
    human_review_url: str = Field(pattern=r"^https://github[.]com/")
    reviews: list[ReviewAttestation] = Field(min_length=5, max_length=5)

    @model_validator(mode="after")
    def validate_reviewers(self) -> ApprovalBundle:
        perspectives = [item.perspective for item in self.reviews]
        if len(set(perspectives)) != 5:
            raise ValueError("all five perspectives required")
        if any(item.commit_sha != self.subject_sha for item in self.reviews):
            raise ValueError("all reviews must target exact commit")
        identities = [item.reviewer for item in self.reviews]
        if len(set(identities)) != 5 or self.author in identities:
            raise ValueError("reviewers must be independent from author and each other")
        if any(item.conclusion != "approve" for item in self.reviews):
            raise ValueError("unresolved reviewer rejection")
        if not self.real_baseline_eligible:
            raise ValueError("real baseline not eligible")
        if self.human_reviewer == self.author:
            raise ValueError("human approver cannot be author")
        return self


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("bundle", type=Path)
    parser.add_argument("--sha", required=True)
    args = parser.parse_args()
    try:
        record = ApprovalBundle.model_validate_json(
            args.bundle.read_text(encoding="utf-8")
        )
        if record.subject_sha != args.sha:
            raise ValueError("commit SHA mismatch")
    except (OSError, ValueError) as exc:
        print(json.dumps({"eligible": False, "reason": str(exc)}))
        return 1
    print(json.dumps({
        "eligible": False,
        "reason": "structural validation only; GitHub identities and CI not authenticated",
    }))
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
