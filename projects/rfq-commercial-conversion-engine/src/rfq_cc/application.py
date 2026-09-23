from __future__ import annotations

from dataclasses import dataclass

from rfq_cc.domain import OrderReference, QuoteReference
from rfq_cc.gates import validate_kt38
from rfq_cc.ports import AuditPort, OrderPort


@dataclass
class ConfirmOrderService:
    orders: OrderPort
    audit: AuditPort

    async def execute(self, quote: QuoteReference) -> OrderReference:
        key = f"{quote.line_id}:Q{quote.quote_version}:CONFIRM_ORDER"
        order = await self.orders.create_order(quote=quote, idempotency_key=key)
        gate = validate_kt38(quote=quote, order=order)

        await self.audit.append(
            line_id=quote.line_id,
            event_type="KT38_VALIDATION",
            payload={
                "idempotency_key": key,
                "order_id": order.order_id,
                "passed": gate.passed,
                "reason_code": gate.reason_code,
            },
        )

        if not gate.passed:
            raise ValueError(f"KT38 blocked: {gate.reason_code}")

        return order
