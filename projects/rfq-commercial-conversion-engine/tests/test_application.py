from decimal import Decimal

import pytest

from rfq_cc.adapters.inmemory import InMemoryAudit, InMemoryOrders
from rfq_cc.application import ConfirmOrderService
from rfq_cc.domain import QuoteReference


@pytest.mark.asyncio
async def test_confirm_order_is_idempotent() -> None:
    orders = InMemoryOrders()
    audit = InMemoryAudit()
    service = ConfirmOrderService(orders=orders, audit=audit)
    quote = QuoteReference(
        line_id="L1",
        quote_id="Q1",
        quote_version=4,
        quantity=Decimal("50"),
        unit_price=Decimal("92"),
        currency="EUR",
    )

    first = await service.execute(quote)
    second = await service.execute(quote)

    assert first.order_id == second.order_id
    assert len(orders.by_key) == 1
    assert len(audit.events) == 2
