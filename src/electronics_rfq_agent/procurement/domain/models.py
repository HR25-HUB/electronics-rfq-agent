from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Annotated
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


PositiveDecimal = Annotated[Decimal, Field(gt=Decimal("0"))]
NonNegativeDecimal = Annotated[Decimal, Field(ge=Decimal("0"))]
CURRENCY_CODE_LENGTH = 3


class IdentityRelation(str, Enum):
    EXACT = "EXACT"
    EQUIVALENT = "EQUIVALENT"
    SUBSTITUTE = "SUBSTITUTE"
    SUPERSEDED = "SUPERSEDED"
    ACCESSORY = "ACCESSORY"
    UNKNOWN = "UNKNOWN"
    REJECTED = "REJECTED"


class SupplierRFQStatus(str, Enum):
    DRAFT = "DRAFT"
    READY = "READY"
    SENT = "SENT"
    COLLECTING_QUOTES = "COLLECTING_QUOTES"
    CLOSED = "CLOSED"
    COMPARING = "COMPARING"
    DECISION_REQUIRED = "DECISION_REQUIRED"
    AWARDED = "AWARDED"
    CANCELLED = "CANCELLED"
    EXPIRED = "EXPIRED"
    NO_QUOTE = "NO_QUOTE"
    NO_AWARD = "NO_AWARD"


class SupplierQuoteStatus(str, Enum):
    RECEIVED = "RECEIVED"
    PARSED = "PARSED"
    NORMALIZED = "NORMALIZED"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"
    ELIGIBLE = "ELIGIBLE"
    REJECTED = "REJECTED"
    EXPIRED = "EXPIRED"


class Eligibility(str, Enum):
    ELIGIBLE = "ELIGIBLE"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"
    REJECTED = "REJECTED"


class AwardOutcome(str, Enum):
    APPROVED = "APPROVED"
    NO_AWARD = "NO_AWARD"


class AwardReason(str, Enum):
    BEST_LANDED_COST = "BEST_LANDED_COST"
    BEST_DELIVERY = "BEST_DELIVERY"
    BEST_PAYMENT_TERMS = "BEST_PAYMENT_TERMS"
    SUPPLIER_RISK = "SUPPLIER_RISK"
    CONTRACTUAL = "CONTRACTUAL"
    CUSTOMER_REQUIREMENT = "CUSTOMER_REQUIREMENT"
    MANUAL_OVERRIDE = "MANUAL_OVERRIDE"
    OTHER = "OTHER"


class SourceEvidence(BaseModel):
    model_config = ConfigDict(frozen=True)

    document_id: uuid.UUID
    sha256: str = Field(min_length=64, max_length=64)
    filename: str = Field(min_length=1)
    mime_type: str = Field(min_length=1)

    fact_key: str = Field(min_length=1)
    sheet: str | None = None
    row: int | None = Field(default=None, ge=1)
    cell_range: str | None = None
    page: int | None = Field(default=None, ge=1)

    original_value: str | None = None
    normalized_value: str | None = None

    extractor: str = Field(min_length=1)
    extracted_at: datetime
    confidence: float = Field(ge=0, le=1)

    @field_validator("sha256")
    @classmethod
    def validate_sha256(cls, value: str) -> str:
        lowered = value.lower()
        if any(ch not in "0123456789abcdef" for ch in lowered):
            raise ValueError("sha256 must contain only hexadecimal characters")
        return lowered


class SupplierRFQLine(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: uuid.UUID
    line_no: int = Field(ge=1)

    requested_part_number: str = Field(min_length=1)
    manufacturer: str | None = None

    quantity: PositiveDecimal
    uom: str = Field(min_length=1)

    required_at: date | None = None
    target_price: PositiveDecimal | None = None
    substitutions_allowed: bool = False


class OfferedIdentity(BaseModel):
    model_config = ConfigDict(frozen=True)

    manufacturer: str | None = None
    manufacturer_part_number: str | None = None
    supplier_sku: str | None = None

    relation: IdentityRelation
    confidence: float = Field(ge=0, le=1)
    evidence_ids: tuple[uuid.UUID, ...] = ()


class SupplierQuoteLine(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: uuid.UUID
    supplier_quote_id: uuid.UUID
    supplier_rfq_line_id: uuid.UUID

    offered_identity: OfferedIdentity

    quoted_quantity: PositiveDecimal
    uom: str = Field(min_length=1)

    moq: PositiveDecimal | None = None
    order_multiple: PositiveDecimal | None = None

    unit_price: PositiveDecimal
    currency: str = Field(min_length=3, max_length=3)

    stock_qty: NonNegativeDecimal | None = None
    lead_time_days: int | None = Field(default=None, ge=0)
    promised_delivery_date: date | None = None

    freight_allocated: NonNegativeDecimal = Decimal("0")
    landed_unit_cost: PositiveDecimal | None = None

    evidence: tuple[SourceEvidence, ...] = ()

    @field_validator("currency")
    @classmethod
    def normalize_currency(cls, value: str) -> str:
        normalized = value.strip().upper()
        if (
            len(normalized) != CURRENCY_CODE_LENGTH
            or not normalized.isalpha()
        ):
            raise ValueError("currency must be a three-letter alphabetic code")
        return normalized

    @model_validator(mode="after")
    def require_price_evidence(self) -> SupplierQuoteLine:
        if not any(item.fact_key == "unit_price" for item in self.evidence):
            raise ValueError("unit_price requires source evidence")
        return self


class SupplierQuote(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: uuid.UUID
    supplier_rfq_id: uuid.UUID
    supplier_inquiry_id: uuid.UUID
    supplier_id: uuid.UUID

    supplier_quote_number: str | None = None
    revision: int = Field(default=1, ge=1)

    received_at: datetime
    valid_until: date | None = None

    currency: str = Field(min_length=3, max_length=3)
    payment_terms_days: int | None = Field(default=None, ge=0)
    incoterm: str | None = None
    freight: NonNegativeDecimal | None = None

    status: SupplierQuoteStatus
    lines: tuple[SupplierQuoteLine, ...]
    source_document_ids: tuple[uuid.UUID, ...]

    @field_validator("currency")
    @classmethod
    def normalize_currency(cls, value: str) -> str:
        normalized = value.strip().upper()
        if (
            len(normalized) != CURRENCY_CODE_LENGTH
            or not normalized.isalpha()
        ):
            raise ValueError("currency must be a three-letter alphabetic code")
        return normalized

    @model_validator(mode="after")
    def require_lines_and_sources(self) -> SupplierQuote:
        if not self.lines:
            raise ValueError("supplier quote requires at least one line")
        if not self.source_document_ids:
            raise ValueError("supplier quote requires at least one source document")
        if any(line.supplier_quote_id != self.id for line in self.lines):
            raise ValueError("all supplier quote lines must reference this quote")
        return self


class ComparisonCandidate(BaseModel):
    model_config = ConfigDict(frozen=True)

    supplier_quote_line_id: uuid.UUID
    eligibility: Eligibility

    landed_cost: Decimal | None = None
    lead_time_days: int | None = Field(default=None, ge=0)
    payment_terms_days: int | None = Field(default=None, ge=0)

    commercial_score: float | None = Field(default=None, ge=0, le=100)
    rejection_reasons: tuple[str, ...] = ()
    evidence_ids: tuple[uuid.UUID, ...] = ()


class CommercialComparison(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: uuid.UUID
    supplier_rfq_line_id: uuid.UUID

    comparison_version: int = Field(ge=1)
    policy_version: str = Field(min_length=1)

    candidates: tuple[ComparisonCandidate, ...]
    recommended_quote_line_id: uuid.UUID | None = None

    created_at: datetime
    trace_id: uuid.UUID

    @model_validator(mode="after")
    def recommendation_must_be_eligible(self) -> CommercialComparison:
        if self.recommended_quote_line_id is None:
            return self
        by_id = {item.supplier_quote_line_id: item for item in self.candidates}
        recommended = by_id.get(self.recommended_quote_line_id)
        if recommended is None:
            raise ValueError("recommended quote line must be present in candidates")
        if recommended.eligibility is not Eligibility.ELIGIBLE:
            raise ValueError("recommended quote line must be eligible")
        return self


class AwardDecision(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: uuid.UUID
    supplier_rfq_line_id: uuid.UUID
    comparison_id: uuid.UUID

    recommended_quote_line_id: uuid.UUID | None = None
    selected_quote_line_id: uuid.UUID | None = None

    outcome: AwardOutcome
    reason_code: AwardReason
    rationale: str | None = None

    policy_version: str = Field(min_length=1)

    decided_by: uuid.UUID
    decided_at: datetime
    is_override: bool
    trace_id: uuid.UUID

    @model_validator(mode="after")
    def validate_selection(self) -> AwardDecision:
        if (
            self.outcome is AwardOutcome.APPROVED
            and self.selected_quote_line_id is None
        ):
            raise ValueError("approved award requires selected_quote_line_id")
        if (
            self.outcome is AwardOutcome.NO_AWARD
            and self.selected_quote_line_id is not None
        ):
            raise ValueError("no-award decision cannot select a quote line")

        expected_override = (
            self.selected_quote_line_id is not None
            and self.recommended_quote_line_id is not None
            and self.selected_quote_line_id != self.recommended_quote_line_id
        )
        if self.is_override != expected_override:
            raise ValueError(
                "is_override must reflect recommendation/selection difference"
            )
        return self
