from __future__ import annotations

from dataclasses import dataclass, field

from rfq_cc.domain import OrderReference, QuoteReference


@dataclass
class InMemoryAudit:
    events: list[dict] = field(default_factory=list)

    async def append(self, *, line_id: str, event_type: str, payload: dict) -> None:
        self.events.append(
            {"line_id": line_id, "event_type": event_type, "payload": payload}
        )


@dataclass
class InMemoryOrders:
    by_key: dict[str, OrderReference] = field(default_factory=dict)

    async def create_order(
        self,
        *,
        quote: QuoteReference,
        idempotency_key: str,
    ) -> OrderReference:
        existing = self.by_key.get(idempotency_key)
        if existing is not None:
            return existing

        order = OrderReference(
            line_id=quote.line_id,
            order_id=f"ORDER-{len(self.by_key) + 1:04d}",
            source_quote_version=quote.quote_version,
            quantity=quote.quantity,
            unit_price=quote.unit_price,
            currency=quote.currency,
        )
        self.by_key[idempotency_key] = order
        return order
