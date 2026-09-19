from __future__ import annotations

import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


EvidenceType = Literal["price", "stock", "lead_time", "quality", "compliance"]
DecisionOutcome = Literal["ACCEPTED", "REVIEW_REQUIRED", "NO_SUPPLIER_FOUND"]


class SupplierEvidence(BaseModel):
    """Source-backed fact used to evaluate a supplier candidate."""

    model_config = ConfigDict(frozen=True)

    evidence_id: uuid.UUID = Field(default_factory=uuid.uuid4)
    supplier_id: str = Field(min_length=1, max_length=100)
    evidence_type: EvidenceType
    source: str = Field(min_length=1, max_length=200)
    source_record_id: str = Field(min_length=1, max_length=200)
    retrieved_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    value: str | int | float | bool | Decimal | None
    confidence: float = Field(ge=0.0, le=1.0)

    @field_validator("retrieved_at")
    @classmethod
    def require_timezone(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("retrieved_at must be timezone-aware")
        return value


class SupplierCandidate(BaseModel):
    """Normalized supplier option derived from evidence."""

    model_config = ConfigDict(frozen=True)

    supplier_id: str = Field(min_length=1, max_length=100)
    unit_price: Decimal = Field(ge=Decimal("0"))
    available_qty: int = Field(ge=0)
    lead_time_days: int = Field(ge=0)
    compliance_ok: bool
    confidence: float = Field(ge=0.0, le=1.0)
    evidence_ids: list[uuid.UUID] = Field(min_length=1)


class SupplierDecision(BaseModel):
    """Terminal, auditable result of the supplier policy."""

    model_config = ConfigDict(frozen=True)

    rfq_line_id: str = Field(min_length=1, max_length=100)
    product_id: str = Field(min_length=1, max_length=200)
    outcome: DecisionOutcome
    selected_supplier_id: str | None = Field(default=None, max_length=100)
    candidate_supplier_ids: list[str]
    confidence: float = Field(ge=0.0, le=1.0)
    evidence_ids: list[uuid.UUID]
    reasons: list[str]
    policy_version: str = "supplier-policy-v0.1"


def evaluate_supplier_candidates(
    *,
    rfq_line_id: str,
    product_id: str,
    requested_qty: int,
    candidates: list[SupplierCandidate],
    min_confidence: float = 0.85,
) -> SupplierDecision:
    """Apply the deterministic SI-001 supplier decision policy.

    This policy is intentionally narrow. It proves the contract and evidence flow;
    it does not create RFQs, purchase orders, or other ERP side effects.
    """
    if requested_qty < 1:
        raise ValueError("requested_qty must be >= 1")
    if not 0.0 <= min_confidence <= 1.0:
        raise ValueError("min_confidence must be between 0 and 1")

    candidate_ids = [candidate.supplier_id for candidate in candidates]
    all_evidence_ids = list(
        dict.fromkeys(
            evidence_id
            for candidate in candidates
            for evidence_id in candidate.evidence_ids
        )
    )

    if not candidates:
        return SupplierDecision(
            rfq_line_id=rfq_line_id,
            product_id=product_id,
            outcome="NO_SUPPLIER_FOUND",
            candidate_supplier_ids=[],
            confidence=0.0,
            evidence_ids=[],
            reasons=["No supplier candidates were provided."],
        )

    eligible = [
        candidate
        for candidate in candidates
        if candidate.compliance_ok
        and candidate.available_qty >= requested_qty
        and candidate.confidence >= min_confidence
    ]

    if not eligible:
        reasons: list[str] = []
        if not any(candidate.compliance_ok for candidate in candidates):
            reasons.append("No candidate passed compliance.")
        if not any(candidate.available_qty >= requested_qty for candidate in candidates):
            reasons.append("No candidate has enough available quantity.")
        if not any(candidate.confidence >= min_confidence for candidate in candidates):
            reasons.append("No candidate meets the confidence threshold.")
        if not reasons:
            reasons.append(
                "No candidate satisfies compliance, quantity, and confidence together."
            )

        return SupplierDecision(
            rfq_line_id=rfq_line_id,
            product_id=product_id,
            outcome="REVIEW_REQUIRED",
            candidate_supplier_ids=candidate_ids,
            confidence=max(candidate.confidence for candidate in candidates),
            evidence_ids=all_evidence_ids,
            reasons=reasons,
        )

    selected = min(
        eligible,
        key=lambda candidate: (
            candidate.unit_price,
            candidate.lead_time_days,
            -candidate.confidence,
            candidate.supplier_id,
        ),
    )

    return SupplierDecision(
        rfq_line_id=rfq_line_id,
        product_id=product_id,
        outcome="ACCEPTED",
        selected_supplier_id=selected.supplier_id,
        candidate_supplier_ids=candidate_ids,
        confidence=selected.confidence,
        evidence_ids=all_evidence_ids,
        reasons=[
            "Selected by deterministic SI-001 policy: compliant, sufficient stock, "
            "confidence threshold met, then lowest price and lead time."
        ],
    )
