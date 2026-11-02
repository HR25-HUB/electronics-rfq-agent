"""Evidence verification must reject modified or missing distributions."""

import tempfile
import unittest
from pathlib import Path

from evidence import create, verify


class EvidenceTests(unittest.TestCase):
    def test_tampered_artifact_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "candidate.whl").write_bytes(b"original")
            manifest = create(
                root, "a" * 40, "https://github.com/owner/repo/actions/runs/1"
            )
            verify(root, manifest)
            (root / "candidate.whl").write_bytes(b"changed")
            with self.assertRaises(ValueError):
                verify(root, manifest)

    def test_missing_artifact_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "candidate.whl").write_bytes(b"original")
            manifest = create(
                root, "a" * 40, "https://github.com/owner/repo/actions/runs/1"
            )
            (root / "candidate.whl").unlink()
            with self.assertRaises(FileNotFoundError):
                verify(root, manifest)

    def test_empty_build_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(ValueError):
                create(Path(directory), "a" * 40, "https://example.com/run/1")


if __name__ == "__main__":
    unittest.main()
