# ruff: noqa: RUF001
from __future__ import annotations

import re
from datetime import UTC, datetime
from enum import StrEnum
from typing import Literal
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field


class DecisionStatus(StrEnum):
    ACCEPT = "ACCEPT"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"
    REJECT = "REJECT"


class MatchRelation(StrEnum):
    NORMALIZED_EXACT = "NORMALIZED_EXACT"
    POSSIBLE_MATCH = "POSSIBLE_MATCH"
    NO_MATCH = "NO_MATCH"


class FailureCode(StrEnum):
    CATALOG_UNAVAILABLE = "CATALOG_UNAVAILABLE"
    AMBIGUOUS_QUANTITY = "AMBIGUOUS_QUANTITY"


class RawRFQLine(BaseModel):
    model_config = ConfigDict(frozen=True)
    rfq_id: str = Field(min_length=1)
    line_id: str = Field(min_length=1)
    raw_text: str = Field(min_length=1)


class NormalizedRFQLine(BaseModel):
    model_config = ConfigDict(frozen=True)
    rfq_id: str
    line_id: str
    raw_text: str
    manufacturer: str | None = None
    part_number_normalized: str | None = None
    quantity: float
    uom: str
    category: str | None = None
    attributes: dict[str, str] = Field(default_factory=dict)


class ProductRecord(BaseModel):
    model_config = ConfigDict(frozen=True)
    product_id: str
    manufacturer: str
    sku: str
    name: str
    category: str
    attributes: dict[str, str] = Field(default_factory=dict)


class EvidenceItem(BaseModel):
    model_config = ConfigDict(frozen=True)
    source: str
    key: str
    value: str


class ProductCandidate(BaseModel):
    model_config = ConfigDict(frozen=True)
    product: ProductRecord
    relation: MatchRelation
    score: float = Field(ge=0.0, le=1.0)
    evidence: tuple[EvidenceItem, ...] = ()


class ProductIdentityDecision(BaseModel):
    model_config = ConfigDict(frozen=True)
    rfq_id: str
    line_id: str
    status: DecisionStatus
    relation: MatchRelation
    canonical_product_id: str | None = None
    confidence: float = Field(ge=0.0, le=1.0)
    evidence: tuple[EvidenceItem, ...] = ()
    policy_reasons: tuple[str, ...] = ()
    candidates: tuple[ProductCandidate, ...] = ()


class ProductIdentityFailure(BaseModel):
    model_config = ConfigDict(frozen=True)
    rfq_id: str
    line_id: str
    failure_code: FailureCode
    message: str
    retryable: bool


class RiskEnvelope(BaseModel):
    model_config = ConfigDict(frozen=True)
    level: Literal["low", "medium", "high"]
    requires_human_approval: bool


class ProductIdentityDecidedEvent(BaseModel):
    model_config = ConfigDict(frozen=True)
    schema_version: str = "1.0.0"
    event_id: UUID = Field(default_factory=uuid4)
    event_type: Literal["rfq.product_identity.decided"] = "rfq.product_identity.decided"
    occurred_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    producer: str = "corporate-rfq-product-identity"
    trace_id: UUID = Field(default_factory=uuid4)
    idempotency_key: str
    payload: ProductIdentityDecision
    risk: RiskEnvelope


class NormalizationError(ValueError):
    pass


class CatalogUnavailable(RuntimeError):
    pass


_MANUFACTURERS = {
    "ABB": "ABB",
    "SCHNEIDER": "Schneider Electric",
    "ШНАЙДЕР": "Schneider Electric",
    "SIEMENS": "Siemens",
    "СИМЕНС": "Siemens",
    "CHINT": "Chint",
    "ЧИНТ": "Chint",
}
_QTY_RE = re.compile(r"(?P<qty>\d+(?:[.,]\d+)?)\s*(?P<uom>шт|pcs?|pieces?|pc)\b", re.IGNORECASE)
_MPN_RE = re.compile(r"\b(?P<mpn>[A-Z]{1,8}[A-Z0-9-]*\d[A-Z0-9-]*(?:\s+[A-Z]\d{1,4})?)\b")
_CURRENT_RE = re.compile(r"\b(?P<current>\d{1,4})\s*[AА]\b", re.IGNORECASE)
_POLES_RE = re.compile(r"\b(?P<poles>[1-4])\s*[PРП]\b", re.IGNORECASE)


def normalize_mpn(value: str) -> str:
    return re.sub(r"[^A-Z0-9]", "", value.upper())


def normalize_rfq_line(raw: RawRFQLine) -> NormalizedRFQLine:
    text = raw.raw_text.strip()
    upper = text.upper().replace("Ё", "Е")
    qty_matches = list(_QTY_RE.finditer(upper))
    if len(qty_matches) != 1:
        raise NormalizationError("Quantity/UOM must be explicit and unambiguous")
    quantity = float(qty_matches[0].group("qty").replace(",", "."))
    if quantity <= 0:
        raise NormalizationError("Quantity must be greater than zero")

    manufacturer = next(
        (canonical for alias, canonical in _MANUFACTURERS.items() if alias in upper),
        None,
    )
    mpn_match = _MPN_RE.search(upper)
    part_norm = normalize_mpn(mpn_match.group("mpn")) if mpn_match else None
    attributes: dict[str, str] = {}
    current = _CURRENT_RE.search(upper)
    poles = _POLES_RE.search(upper)
    if current:
        attributes["current"] = f"{current.group('current')}A"
    if poles:
        attributes["poles"] = f"{poles.group('poles')}P"

    return NormalizedRFQLine(
        rfq_id=raw.rfq_id,
        line_id=raw.line_id,
        raw_text=raw.raw_text,
        manufacturer=manufacturer,
        part_number_normalized=part_norm,
        quantity=quantity,
        uom="pcs",
        category=("circuit_breaker" if "АВТОМАТ" in upper or "CIRCUIT BREAKER" in upper else None),
        attributes=attributes,
    )
