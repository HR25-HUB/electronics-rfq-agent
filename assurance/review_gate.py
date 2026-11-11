"""Fail-closed gate: absence of independent evidence is a failure."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path

from .review_contract import Evidence, Perspective, Review

REQUIRED = ("ruff", "typecheck", "pytest", "requirements_traceability")


def _review_errors(record: Evidence) -> list[str]:
    errors: list[str] = []
    completed = [review for review in record.reviews if review.completed]
    counts = Counter(review.perspective for review in completed)
    for perspective in Perspective:
        if counts[perspective] != 1:
            errors.append(f"missing/duplicate review: {perspective.value}")
    if len({review.session_id for review in completed}) != len(completed):
        errors.append("review sessions are not distinct")
    manifests = [review.artifact_sha256 for review in completed]
    if manifests and any(manifest != manifests[0] for manifest in manifests):
        errors.append("reviewers used different artifact manifests")
    ids = [finding.id for review in record.reviews for finding in review.findings]
    if len(ids) != len(set(ids)):
        errors.append("duplicate finding IDs")
    return errors


def _artifact_errors(review: Review, root: Path) -> list[str]:
    errors: list[str] = []
    for filename, digest in review.artifact_sha256.items():
        path = (root / filename).resolve()
        if not path.is_relative_to(root.resolve()) or not path.is_file():
            errors.append(f"missing/unsafe artifact: {filename}")
        elif hashlib.sha256(path.read_bytes()).hexdigest() != digest:
            errors.append(f"artifact hash mismatch: {filename}")
    return errors


def _finding_errors(review: Review) -> list[str]:
    errors: list[str] = []
    for finding in review.findings:
        if finding.perspective != review.perspective:
            errors.append(f"invalid finding perspective: {finding.id}")
        if finding.severity == "blocker" and finding.disposition != "fixed":
            errors.append(f"unresolved blocker: {finding.id}")
        if finding.severity == "major" and finding.disposition == "open":
            errors.append(f"unresolved major: {finding.id}")
    return errors


def evaluate(record: Evidence, root: Path, expected_sha: str) -> list[str]:
    errors = _review_errors(record)
    if record.commit_sha != expected_sha:
        errors.append("commit SHA mismatch")
    for review in record.reviews:
        if review.reviewer == record.designer or not review.independent_context:
            errors.append("review independence not established")
        errors.extend(_artifact_errors(review, root))
        errors.extend(_finding_errors(review))
    for check in REQUIRED:
        if record.checks.get(check) is not True:
            errors.append(f"missing CI check: {check}")
    if any(not references for references in record.requirements.values()):
        errors.append("untraced requirement")
    if record.evaluation.failed:
        errors.append("evaluation failures")
    if record.evaluation.synthetic:
        errors.append("synthetic eval is not production evidence")
    if not record.human_approved or not record.human_approver:
        errors.append("human approval missing")
    return sorted(set(errors))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("evidence", type=Path)
    parser.add_argument("--sha", required=True)
    args = parser.parse_args()
    try:
        record = Evidence.model_validate_json(args.evidence.read_text(encoding="utf-8"))
        errors = evaluate(record, Path.cwd(), args.sha)
    except (OSError, ValueError) as exc:
        errors = [f"invalid evidence: {exc}"]
    print(json.dumps({"passed": not errors, "errors": errors}, indent=2))
    return int(bool(errors))


if __name__ == "__main__":
    raise SystemExit(main())
