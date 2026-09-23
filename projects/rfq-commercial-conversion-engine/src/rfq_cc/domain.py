from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from enum import StrEnum

from pydantic import BaseModel, Field


class NeedContext(StrEnum):
    PROJECT = "PROJECT"
    STOCK_REPLENISHMENT = "STOCK_REPLENISHMENT"
    RESALE = "RESALE"
    PRICE_MONITORING = "PRICE_MONITORING"
    UNKNOWN = "UNKNOWN"


class PrimaryCriterion(StrEnum):
    LOWEST_UNIT_PRICE = "LOWEST_UNIT_PRICE"
    FULL_COMPLETION = "FULL_COMPLETION"
    PAYMENT_TERMS = "PAYMENT_TERMS"
    DELIVERY_DEADLINE = "DELIVERY_DEADLINE"
    TECHNICAL_MATCH = "TECHNICAL_MATCH"
    UNKNOWN = "UNKNOWN"


class QualificationClass(StrEnum):
    HOT = "HOT"
    WARM = "WARM"
    COLD_CALCULATION = "COLD_CALCULATION"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"


class ResponseKind(StrEnum):
    APPROVED_FULL = "APPROVED_FULL"
    APPROVED_PARTIAL = "APPROVED_PARTIAL"
    PRICE_OBJECTION = "PRICE_OBJECTION"
    DELIVERY_OBJECTION = "DELIVERY_OBJECTION"
    PAYMENT_TERMS_OBJECTION = "PAYMENT_TERMS_OBJECTION"
    PRODUCT_OBJECTION = "PRODUCT_OBJECTION"
    COMPETITOR = "COMPETITOR"
    DEFERRED = "DEFERRED"
    REJECTED = "REJECTED"
    UNKNOWN = "UNKNOWN"


class CommitmentLevel(StrEnum):
    NONE = "NONE"
    INTEREST = "INTEREST"
    CONDITIONAL = "CONDITIONAL"
    EXPLICIT_ORDER = "EXPLICIT_ORDER"


class CommercialAction(StrEnum):
    PASS_KT37 = "PASS_KT37"
    REQUEST_TARGET_PRICE = "REQUEST_TARGET_PRICE"
    REPRICE = "REPRICE"
    CHANGE_PAYMENT_TERMS = "CHANGE_PAYMENT_TERMS"
    PRODUCT_REIDENTIFICATION = "PRODUCT_REIDENTIFICATION"
    FOLLOW_UP = "FOLLOW_UP"
    MARK_LOST = "MARK_LOST"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"


class QualificationInput(BaseModel):
    line_id: str
    deal_id: str
    need_context: NeedContext = NeedContext.UNKNOWN
    primary_criterion: PrimaryCriterion = PrimaryCriterion.UNKNOWN
    decision_deadline_known: bool = False
    decision_maker_known: bool = False
    budget_process_known: bool = False
    competitors_known: bool = False
    explicit_project_or_need: bool = False
    customer_engaged_in_dialogue: bool = False
    agreed_success_condition: bool = False


class QualificationSnapshot(QualificationInput):
    score: int = Field(ge=0, le=100)
    classification: QualificationClass
    missing_fields: list[str] = Field(default_factory=list)


class ResourceBudget(BaseModel):
    max_manual_minutes: int
    supplier_target_count: int
    expert_review_allowed: bool
    mandatory_presentation: bool


class CustomerIntent(BaseModel):
    response_kind: ResponseKind
    commitment: CommitmentLevel = CommitmentLevel.NONE
    confidence: float = Field(ge=0, le=1)
    requested_quantity: Decimal | None = Field(default=None, gt=0)
    target_price: Decimal | None = Field(default=None, gt=0)
    requested_payment_days: int | None = Field(default=None, ge=0)
    evidence_spans: list[str] = Field(default_factory=list)


class CommercialDecision(BaseModel):
    action: CommercialAction
    reason_code: str
    return_checkpoint: str | None = None
    requires_human: bool = True


class QuoteReference(BaseModel):
    line_id: str
    quote_id: str
    quote_version: int = Field(ge=1)
    quantity: Decimal = Field(gt=0)
    unit_price: Decimal = Field(gt=0)
    currency: str


class CustomerDecisionEvidence(BaseModel):
    decision_id: str
    line_id: str
    quote_id: str
    quote_version: int = Field(ge=1)
    interaction_id: str
    response_kind: ResponseKind
    evidence_text: str
    decided_at: datetime


class OrderReference(BaseModel):
    line_id: str
    order_id: str
    source_quote_version: int = Field(ge=1)
    quantity: Decimal = Field(gt=0)
    unit_price: Decimal = Field(gt=0)
    currency: str


class GateResult(BaseModel):
    passed: bool
    reason_code: str
