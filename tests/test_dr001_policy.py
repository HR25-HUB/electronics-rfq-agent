"""DR-001 regression: unapproved substitutions must not become priced quotes."""

from __future__ import annotations

from decimal import Decimal

import pytest

from electronics_rfq_agent.agent import QuoteAgent
from electronics_rfq_agent.mcp.base import ERPMCPServer
from electronics_rfq_agent.models import ERPPartResult, RFQLineItem


class CandidateERP(ERPMCPServer):
    def __init__(self, exact: ERPPartResult | None, candidate: ERPPartResult | None):
        self.exact = exact
        self.candidate = candidate
        self.price_calls = 0

    async def get_part(self, part_number: str) -> ERPPartResult | None:
        return self.exact

    async def search_parts(self, query: str, limit: int = 20) -> list[ERPPartResult]:
        return [self.candidate] if self.candidate else []

    async def get_price(self, part_number: str, quantity: int) -> Decimal | None:
        self.price_calls += 1
        return Decimal("10.00")


def part(number: str) -> ERPPartResult:
    return ERPPartResult(
        part_number=number,
        description="Synthetic regression part",
        manufacturer="SYNTHETIC",
        unit_price=Decimal("10.00"),
        available_qty=100,
        lead_time_days=2,
    )


@pytest.mark.asyncio
async def test_unapproved_alternative_is_not_quoted() -> None:
    erp = CandidateERP(exact=None, candidate=part("ALT-100"))
    rfq = RFQLineItem(line_number=1, part_number="REQ-100", quantity=3)
    result = await QuoteAgent(erp=erp)._lookup_line(rfq)
    assert result.status == "not_found"
    assert result.erp_result is None
    assert result.unit_price is None
    assert result.extended_price is None
    assert "manual approval required" in (result.notes or "")
    assert erp.price_calls == 0


@pytest.mark.asyncio
async def test_exact_match_is_still_quoted() -> None:
    erp = CandidateERP(exact=part("REQ-100"), candidate=None)
    rfq = RFQLineItem(line_number=1, part_number="REQ-100", quantity=3)
    result = await QuoteAgent(erp=erp)._lookup_line(rfq)
    assert result.status == "found"
    assert result.unit_price is not None
    assert erp.price_calls == 1


@pytest.mark.asyncio
async def test_case_insensitive_exact_catalog_hit_is_quoted() -> None:
    erp = CandidateERP(exact=None, candidate=part("req-100"))
    rfq = RFQLineItem(line_number=1, part_number="REQ-100", quantity=3)
    result = await QuoteAgent(erp=erp)._lookup_line(rfq)
    assert result.status == "found"
    assert erp.price_calls == 1


@pytest.mark.asyncio
async def test_missing_part_is_not_quoted() -> None:
    erp = CandidateERP(exact=None, candidate=None)
    rfq = RFQLineItem(line_number=1, part_number="REQ-100", quantity=3)
    result = await QuoteAgent(erp=erp)._lookup_line(rfq)
    assert result.status == "not_found"
    assert result.unit_price is None
    assert erp.price_calls == 0
