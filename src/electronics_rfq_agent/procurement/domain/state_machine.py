from __future__ import annotations

from electronics_rfq_agent.procurement.domain.models import SupplierRFQStatus


class InvalidSupplierRFQTransition(ValueError):
    """Raised when a Supplier RFQ lifecycle transition is not permitted."""


_ALLOWED_TRANSITIONS: dict[SupplierRFQStatus, frozenset[SupplierRFQStatus]] = {
    SupplierRFQStatus.DRAFT: frozenset(
        {
            SupplierRFQStatus.READY,
            SupplierRFQStatus.CANCELLED,
        }
    ),
    SupplierRFQStatus.READY: frozenset(
        {
            SupplierRFQStatus.SENT,
            SupplierRFQStatus.CANCELLED,
        }
    ),
    SupplierRFQStatus.SENT: frozenset(
        {
            SupplierRFQStatus.COLLECTING_QUOTES,
            SupplierRFQStatus.CANCELLED,
            SupplierRFQStatus.EXPIRED,
        }
    ),
    SupplierRFQStatus.COLLECTING_QUOTES: frozenset(
        {
            SupplierRFQStatus.CLOSED,
            SupplierRFQStatus.NO_QUOTE,
            SupplierRFQStatus.CANCELLED,
            SupplierRFQStatus.EXPIRED,
        }
    ),
    SupplierRFQStatus.CLOSED: frozenset(
        {
            SupplierRFQStatus.COMPARING,
            SupplierRFQStatus.NO_QUOTE,
            SupplierRFQStatus.CANCELLED,
        }
    ),
    SupplierRFQStatus.COMPARING: frozenset(
        {
            SupplierRFQStatus.DECISION_REQUIRED,
            SupplierRFQStatus.NO_AWARD,
        }
    ),
    SupplierRFQStatus.DECISION_REQUIRED: frozenset(
        {
            SupplierRFQStatus.AWARDED,
            SupplierRFQStatus.NO_AWARD,
        }
    ),
    SupplierRFQStatus.AWARDED: frozenset(),
    SupplierRFQStatus.CANCELLED: frozenset(),
    SupplierRFQStatus.EXPIRED: frozenset(),
    SupplierRFQStatus.NO_QUOTE: frozenset(),
    SupplierRFQStatus.NO_AWARD: frozenset(),
}


def allowed_transitions(status: SupplierRFQStatus) -> frozenset[SupplierRFQStatus]:
    return _ALLOWED_TRANSITIONS[status]


def transition_supplier_rfq(
    current: SupplierRFQStatus,
    target: SupplierRFQStatus,
    *,
    line_count: int,
    supplier_count: int,
) -> SupplierRFQStatus:
    if target not in allowed_transitions(current):
        raise InvalidSupplierRFQTransition(
            f"transition {current.value} -> {target.value} is not allowed"
        )

    if target is SupplierRFQStatus.READY and line_count < 1:
        raise InvalidSupplierRFQTransition(
            "Supplier RFQ requires at least one line before READY"
        )

    if target is SupplierRFQStatus.SENT:
        if line_count < 1:
            raise InvalidSupplierRFQTransition(
                "Supplier RFQ requires at least one line before SENT"
            )
        if supplier_count < 1:
            raise InvalidSupplierRFQTransition(
                "Supplier RFQ requires at least one supplier before SENT"
            )

    return target
