from __future__ import annotations

from decimal import Decimal

from electronics_rfq_agent.procurement.domain.models import (
    Eligibility,
    IdentityRelation,
    SupplierQuoteLine,
    SupplierRFQLine,
)


def _has_conflicting_evidence(line: SupplierQuoteLine) -> bool:
    values_by_fact: dict[str, set[str]] = {}
    for evidence in line.evidence:
        if evidence.normalized_value is None:
            continue
        values_by_fact.setdefault(evidence.fact_key, set()).add(
            evidence.normalized_value
        )
    return any(len(values) > 1 for values in values_by_fact.values())


def evaluate_candidate(
    requested: SupplierRFQLine,
    offered: SupplierQuoteLine,
) -> tuple[Eligibility, tuple[str, ...]]:
    """Apply deterministic pre-scoring eligibility gates.

    This function deliberately does not rank suppliers and cannot award a quote.
    """
    reasons: list[str] = []

    if offered.supplier_rfq_line_id != requested.id:
        return Eligibility.REJECTED, ("RFQ_LINE_MISMATCH",)

    if _has_conflicting_evidence(offered):
        reasons.append("CONFLICTING_EVIDENCE")

    relation = offered.offered_identity.relation
    if relation in {
        IdentityRelation.UNKNOWN,
        IdentityRelation.REJECTED,
        IdentityRelation.ACCESSORY,
    }:
        return Eligibility.REJECTED, (f"IDENTITY_{relation.value}",)

    if relation in {
        IdentityRelation.SUBSTITUTE,
        IdentityRelation.EQUIVALENT,
        IdentityRelation.SUPERSEDED,
    }:
        reasons.append(f"IDENTITY_{relation.value}")

    if offered.moq is not None and offered.moq > requested.quantity:
        reasons.append("MOQ_EXCEEDS_REQUESTED_QUANTITY")

    if offered.quoted_quantity < requested.quantity:
        reasons.append("INSUFFICIENT_QUOTED_QUANTITY")

    if reasons:
        return Eligibility.REVIEW_REQUIRED, tuple(reasons)

    return Eligibility.ELIGIBLE, ()


def extended_cost(line: SupplierQuoteLine) -> Decimal:
    unit_cost = line.landed_unit_cost or (line.unit_price + line.freight_allocated)
    return unit_cost * line.quoted_quantity
