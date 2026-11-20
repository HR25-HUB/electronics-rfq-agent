"""Isolated benchmark oracle. Run explicitly with pytest -o addopts=.

Baseline is expected to fail the non-ASCII preservation assertion.
"""

import json

from electronics_rfq_agent.parser import RFQParser

CONTROL_QUANTITY = 10
CYRILLIC_QUANTITY = 200
CYRILLIC_PART_NUMBER = "\u0412\u041a-21300531"


def test_control_ascii_line_parses():
    rows = [{"line_number": 1, "part_number": "ABC-123", "quantity": CONTROL_QUANTITY}]
    result = RFQParser()._parse_json_response(json.dumps(rows))
    assert len(result) == 1
    assert result[0].part_number == "ABC-123"
    assert result[0].quantity == CONTROL_QUANTITY


def test_non_ascii_item_is_not_silently_dropped():
    """A client RFQ item must not disappear from the parsed collection."""
    rows = [
        {"line_number": 1, "part_number": "ABC-123", "quantity": CONTROL_QUANTITY},
        {
            "line_number": 2,
            "part_number": CYRILLIC_PART_NUMBER,
            "quantity": CYRILLIC_QUANTITY,
        },
    ]
    result = RFQParser()._parse_json_response(json.dumps(rows, ensure_ascii=False))
    assert len(result) == 2, "RFQ line lost during parsing"
    assert [item.line_number for item in result] == [1, 2]
    assert result[1].part_number == CYRILLIC_PART_NUMBER
    assert result[1].quantity == CYRILLIC_QUANTITY
