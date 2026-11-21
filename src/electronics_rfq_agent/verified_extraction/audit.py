"""Reproducible, no-overwrite audit artifacts for synthetic RFQ extraction."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Any

from pydantic import BaseModel


def canonical_json(data: Any) -> bytes:
    if isinstance(data, BaseModel):
        data = data.model_dump(mode="json")
    payload = json.dumps(
        data, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    )
    return (payload + "\n").encode("utf-8")


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def result_hash(result: BaseModel) -> str:
    return sha256(canonical_json(result))


def reproducibility_key(
    input_hash: str, output_hash: str, policy_version: str, code_version: str
) -> str:
    data = {
        "input_sha256": input_hash,
        "output_sha256": output_hash,
        "policy_version": policy_version,
        "code_version": code_version,
    }
    return sha256(canonical_json(data))


def write_audit(  # noqa: PLR0913
    root: Path,
    run_id: str,
    *,
    evidence: BaseModel,
    result: BaseModel,
    report: BaseModel,
    policy_version: str,
    code_version: str,
) -> Path:
    """Create a new directory exclusively; never replace an existing audit run.

    A failure may leave a partial run; verification will reject its missing manifest.
    Do not call this with sensitive documents in a public checkout.
    """
    if not run_id or not all(c.isalnum() or c in "-_" for c in run_id):
        raise ValueError("invalid_run_id")
    root.mkdir(parents=True, exist_ok=True)
    target = root / run_id
    target.mkdir(exist_ok=False)
    files = {
        "input-evidence.json": canonical_json(evidence),
        "extraction-result.json": canonical_json(result),
        "verification-report.json": canonical_json(report),
    }
    input_hash = sha256(files["input-evidence.json"])
    output_hash = sha256(files["extraction-result.json"])
    metadata = {
        "run_id": run_id,
        "input_sha256": input_hash,
        "output_sha256": output_hash,
        "policy_version": policy_version,
        "code_version": code_version,
        "reproducibility_key": reproducibility_key(
            input_hash, output_hash, policy_version, code_version
        ),
    }
    files["run-metadata.json"] = canonical_json(metadata)
    checksums = {name: sha256(value) for name, value in sorted(files.items())}
    files["manifest.json"] = canonical_json({
        "schema_version": "1.0.0",
        "files_sha256": checksums,
    })
    for name, data in files.items():
        path = target / name
        with path.open("xb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
    return target


def verify_audit(target: Path) -> bool:
    try:
        manifest = json.loads((target / "manifest.json").read_text(encoding="utf-8"))
        checksums = manifest["files_sha256"]
        if not isinstance(checksums, dict):
            return False
        required = {
            "input-evidence.json", "extraction-result.json",
            "verification-report.json", "run-metadata.json",
        }
        if set(checksums) != required:
            return False
        return all(
            sha256((target / name).read_bytes()) == expected
            for name, expected in checksums.items()
        )
    except (OSError, ValueError, KeyError, TypeError):
        return False
