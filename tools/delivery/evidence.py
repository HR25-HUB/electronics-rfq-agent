"""Create and verify SHA-256 manifests; manifests are not signed attestations."""

from __future__ import annotations

import hashlib
import json
import os
import re
import sys
from pathlib import Path
from typing import Any


def create(root: Path, commit: str, run_url: str) -> dict[str, Any]:
    if not re.fullmatch(r"[0-9a-f]{40}", commit):
        raise ValueError("Expected a full commit SHA")
    files = sorted([*root.glob("*.whl"), *root.glob("*.tar.gz")])
    if not files:
        raise ValueError("No built distributions")
    return {
        "schema_version": 1,
        "commit_sha": commit,
        "run_url": run_url,
        "artifacts": [
            {"name": path.name, "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
            for path in files
        ],
        "production_changed": False,
        "provenance": "GitHub Actions run reference; not a signed attestation",
    }


def verify(root: Path, manifest: dict[str, Any]) -> None:
    if not manifest.get("artifacts"):
        raise ValueError("Empty artifact manifest")
    for artifact in manifest["artifacts"]:
        name = artifact["name"]
        if Path(name).name != name or "/" in name or "\\" in name:
            raise ValueError("Artifact must be a plain filename")
        digest = hashlib.sha256((root / name).read_bytes()).hexdigest()
        if digest != artifact["sha256"]:
            raise ValueError(f"Digest mismatch: {name}")


if __name__ == "__main__":
    distribution = Path("dist")
    manifest_path = distribution / "release-evidence.json"
    if sys.argv[1:] == ["verify"]:
        data = json.loads(manifest_path.read_text(encoding="utf-8"))
        verify(distribution, data)
    else:
        server = os.environ["GITHUB_SERVER_URL"]
        repository = os.environ["GITHUB_REPOSITORY"]
        run = os.environ["GITHUB_RUN_ID"]
        attempt = os.environ["GITHUB_RUN_ATTEMPT"]
        data = create(
            distribution,
            os.environ["GITHUB_SHA"],
            f"{server}/{repository}/actions/runs/{run}/attempts/{attempt}",
        )
        data["pr_head_sha"] = os.environ.get("PR_HEAD_SHA")
        data["gate_results"] = json.loads(os.environ["GATE_RESULTS"])
        if set(data["gate_results"]) != {
            "quality",
            "extras-compat",
            "policy",
            "secrets",
        }:
            raise ValueError("Missing or unexpected prerequisite gate")
        if any(value["result"] != "success" for value in data["gate_results"].values()):
            raise ValueError("All prerequisite gates must succeed")
        manifest_path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
        verify(distribution, data)
    print("Distribution digests verified")
