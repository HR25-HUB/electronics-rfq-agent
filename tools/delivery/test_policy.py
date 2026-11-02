"""Negative controls for the delivery architecture gate (stdlib only)."""

import tempfile
import unittest
from pathlib import Path

from architecture import check


class ArchitectureTests(unittest.TestCase):
    def inspect(self, name: str, source: str) -> list[str]:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / "src/electronics_rfq_agent" / name
            path.parent.mkdir(parents=True)
            path.write_text(source, encoding="utf-8")
            return check(root)

    def test_models_accept_domain_types(self):
        self.assertEqual(
            self.inspect("models.py", "from pydantic import BaseModel"), []
        )

    def test_models_reject_network_dependency(self):
        self.assertTrue(self.inspect("models.py", "import httpx"))

    def test_models_reject_nested_internal_import(self):
        source = "def f():\n    import electronics_rfq_agent.agent"
        self.assertTrue(self.inspect("models.py", source))

    def test_adapter_rejects_relative_orchestration_import(self):
        self.assertTrue(self.inspect("mcp/epicor.py", "from .. import agent"))

    def test_parser_rejects_adapter_dependency(self):
        source = "from electronics_rfq_agent.mcp.base import ERPMCPServer"
        self.assertTrue(self.inspect("parser.py", source))

    def test_adapter_accepts_contract(self):
        source = "from ..models import ERPPartResult"
        self.assertEqual(self.inspect("mcp/epicor.py", source), [])

    def test_adapter_rejects_root_facade(self):
        source = "from electronics_rfq_agent import QuoteAgent"
        self.assertTrue(self.inspect("mcp/epicor.py", source))

    def test_parser_rejects_root_adapter_reexport(self):
        source = "from electronics_rfq_agent import MockERP"
        self.assertTrue(self.inspect("parser.py", source))

    def test_syntax_error_fails_closed(self):
        self.assertTrue(self.inspect("models.py", "def broken("))

    def test_missing_package_fails_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            self.assertTrue(check(Path(directory)))


if __name__ == "__main__":
    unittest.main()
