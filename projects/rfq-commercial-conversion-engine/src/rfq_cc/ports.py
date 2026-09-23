from __future__ import annotations

from typing import Protocol

from rfq_cc.domain import OrderReference, QuoteReference


class AuditPort(Protocol):
    async def append(self, *, line_id: str, event_type: str, payload: dict) -> None: ...


class OrderPort(Protocol):
    async def create_order(
        self,
        *,
        quote: QuoteReference,
        idempotency_key: str,
    ) -> OrderReference: ...


class InteractionPort(Protocol):
    async def add_timeline_note(self, *, deal_id: str, text: str) -> None: ...
