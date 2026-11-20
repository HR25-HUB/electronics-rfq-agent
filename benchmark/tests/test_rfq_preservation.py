"""Independent benchmark tests. Deliberately outside pyproject pytest testpaths.

The baseline is EXPECTED to fail the second test, but must not be changed here.
Run explicitly: uv run pytest -q -o addopts= benchmark/tests/test_rfq_preservation.py
"""
import json

from electronics_rfq_agent.parser import RFQParser


def test_control_ascii_line_parses():
    rows = [{"line_number": 1, "part_number": "ABC-123", "quantity": 10}]
    result = RFQParser()._parse_json_response(json.dumps(rows))
    assert len(result) == 1
    assert result[0].part_number == "ABC-123"
    assert result[0].quantity == 10


def test_non_ascii_item_is_not_silently_dropped():
    """A real RFQ line cannot disappear from the resulting item collection."""
    rows = [
        {"line_number": 1, "part_number": "ABC-123", "quantity": 10},
        {"line_number": 2, "part_number": "ВК-21300531", "quantity": 200},
    ]
    result = RFQParser()._parse_json_response(
        json.dumps(rows, ensure_ascii=False)
    )
    assert len(result) == 2, "RFQ line lost during parsing"
    assert [item.line_number for item in result] == [1, 2]
    assert result[1].part_number == "ВК-21300531"
    assert result[1].quantity == 200
