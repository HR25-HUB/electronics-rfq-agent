"""Fail-closed gate: absence of independent evidence is a failure."""
from __future__ import annotations
import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path
from .review_contract import Evidence, Perspective

REQUIRED = ("ruff", "typecheck", "pytest", "requirements_traceability")

def evaluate(record: Evidence, root: Path, expected_sha: str) -> list[str]:
    failures: list[str] = []
    if record.commit_sha != expected_sha:
        failures.append("commit SHA mismatch")
    reviews = [r for r in record.reviews if r.completed]
    counts = Counter(r.perspective for r in reviews)
    for perspective in Perspective:
        if counts[perspective] != 1:
            failures.append(f"missing/duplicate review: {perspective.value}")
    if len({r.session_id for r in reviews}) != len(reviews):
        failures.append("review sessions are not distinct")
    manifests = [r.artifact_sha256 for r in reviews]
    if manifests and any(x != manifests[0] for x in manifests):
        failures.append("reviewers used different artifact manifests")
    for review in record.reviews:
        if review.reviewer == record.designer or not review.independent_context:
            failures.append("review independence not established")
        for filename, digest in review.artifact_sha256.items():
            path = (root / filename).resolve()
            if not path.is_relative_to(root.resolve()) or not path.is_file():
                failures.append(f"missing/unsafe artifact: {filename}")
            elif hashlib.sha256(path.read_bytes()).hexdigest() != digest:
                failures.append(f"artifact hash mismatch: {filename}")
        for f in review.findings:
            if f.perspective != review.perspective:
                failures.append(f"invalid finding perspective: {f.id}")
            if f.severity == "blocker" and f.disposition != "fixed":
                failures.append(f"unresolved blocker: {f.id}")
            if f.severity == "major" and f.disposition == "open":
                failures.append(f"unresolved major: {f.id}")
    ids = [f.id for r in record.reviews for f in r.findings]
    if len(ids) != len(set(ids)):
        failures.append("duplicate finding IDs")
    for check in REQUIRED:
        if record.checks.get(check) is not True:
            failures.append(f"missing CI check: {check}")
    if any(not references for references in record.requirements.values()):
        failures.append("untraced requirement")
    if record.evaluation.failed:
        failures.append("evaluation failures")
    if record.evaluation.synthetic:
        failures.append("synthetic eval is not production evidence")
    if not record.human_approved or not record.human_approver:
        failures.append("human approval missing")
    return sorted(set(failures))

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
