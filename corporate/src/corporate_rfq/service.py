from __future__ import annotations

from typing import Protocol

from corporate_rfq.models import (
    CatalogUnavailable,
    DecisionStatus,
    EvidenceItem,
    FailureCode,
    MatchRelation,
    NormalizationError,
    NormalizedRFQLine,
    ProductCandidate,
    ProductIdentityDecidedEvent,
    ProductIdentityDecision,
    ProductIdentityFailure,
    ProductRecord,
    RawRFQLine,
    RiskEnvelope,
    normalize_mpn,
    normalize_rfq_line,
)


class CatalogPort(Protocol):
    def find_normalized_exact(
        self, *, normalized_mpn: str, manufacturer: str | None
    ) -> ProductRecord | None: ...
    def retrieve_candidates(
        self, line: NormalizedRFQLine, *, limit: int = 5
    ) -> list[ProductCandidate]: ...


_CRITICAL_ATTRIBUTES = ("poles", "current")


def _critical_attribute_conflicts(
    line: NormalizedRFQLine, product: ProductRecord
) -> tuple[EvidenceItem, ...]:
    conflicts: list[EvidenceItem] = []
    for key in _CRITICAL_ATTRIBUTES:
        requested = line.attributes.get(key)
        catalog_value = product.attributes.get(key)
        if requested and catalog_value and requested != catalog_value:
            conflicts.append(
                EvidenceItem(
                    source="policy",
                    key=f"critical_attribute_conflict.{key}",
                    value=f"requested={requested};catalog={catalog_value}",
                )
            )
    return tuple(conflicts)


def _pre_accept_review_reasons(line: NormalizedRFQLine) -> tuple[str, ...]:
    reasons: list[str] = []
    if line.manufacturer is None:
        reasons.append("manufacturer is not proven")
    if "analogue_or_replacement_intent" in line.policy_flags:
        reasons.append("analogue/replacement intent requires separate human decision")
    if "low_confidence_evidence" in line.policy_flags:
        reasons.append("low-confidence source evidence blocks automatic acceptance")
    return tuple(reasons)


def _exact_candidate(product: ProductRecord) -> ProductCandidate:
    return ProductCandidate(
        product=product,
        relation=MatchRelation.NORMALIZED_EXACT,
        score=1.0,
        evidence=(EvidenceItem(source="catalog", key="canonical_sku", value=product.sku),),
    )


class ResolveProductIdentity:
    def __init__(self, catalog: CatalogPort) -> None:
        self._catalog = catalog

    def execute(self, raw: RawRFQLine) -> ProductIdentityDecision | ProductIdentityFailure:
        try:
            line = normalize_rfq_line(raw)
        except NormalizationError as exc:
            return ProductIdentityFailure(
                rfq_id=raw.rfq_id,
                line_id=raw.line_id,
                failure_code=FailureCode.AMBIGUOUS_QUANTITY,
                message=str(exc),
                retryable=False,
            )

        try:
            if line.part_number_normalized:
                product = self._catalog.find_normalized_exact(
                    normalized_mpn=line.part_number_normalized,
                    manufacturer=line.manufacturer,
                )
                if product is not None:
                    review_reasons = _pre_accept_review_reasons(line)
                    if review_reasons:
                        return ProductIdentityDecision(
                            rfq_id=line.rfq_id,
                            line_id=line.line_id,
                            status=DecisionStatus.REVIEW_REQUIRED,
                            relation=MatchRelation.NORMALIZED_EXACT,
                            canonical_product_id=None,
                            confidence=1.0,
                            evidence=tuple(
                                EvidenceItem(
                                    source="policy",
                                    key="pre_accept_review",
                                    value=reason,
                                )
                                for reason in review_reasons
                            ),
                            policy_reasons=review_reasons,
                            candidates=(_exact_candidate(product),),
                        )

                    conflicts = _critical_attribute_conflicts(line, product)
                    if conflicts:
                        return ProductIdentityDecision(
                            rfq_id=line.rfq_id,
                            line_id=line.line_id,
                            status=DecisionStatus.REJECT,
                            relation=MatchRelation.NORMALIZED_EXACT,
                            canonical_product_id=None,
                            confidence=0.0,
                            evidence=conflicts,
                            policy_reasons=(
                                "critical attribute conflict blocks automatic product identity",
                            ),
                        )

                    return ProductIdentityDecision(
                        rfq_id=line.rfq_id,
                        line_id=line.line_id,
                        status=DecisionStatus.ACCEPT,
                        relation=MatchRelation.NORMALIZED_EXACT,
                        canonical_product_id=product.product_id,
                        confidence=1.0,
                        evidence=(
                            EvidenceItem(
                                source="catalog",
                                key="normalized_mpn",
                                value=line.part_number_normalized,
                            ),
                            EvidenceItem(source="catalog", key="canonical_sku", value=product.sku),
                        ),
                        policy_reasons=("unique normalized exact catalog match",),
                    )

            candidates = self._catalog.retrieve_candidates(line, limit=5)
            return ProductIdentityDecision(
                rfq_id=line.rfq_id,
                line_id=line.line_id,
                status=DecisionStatus.REVIEW_REQUIRED,
                relation=candidates[0].relation if candidates else MatchRelation.NO_MATCH,
                canonical_product_id=None,
                confidence=candidates[0].score if candidates else 0.0,
                policy_reasons=(
                    (
                        "non-exact candidate must not be auto-approved"
                        if candidates
                        else "no catalog match; human review required"
                    ),
                ),
                candidates=tuple(candidates),
            )
        except CatalogUnavailable as exc:
            return ProductIdentityFailure(
                rfq_id=raw.rfq_id,
                line_id=raw.line_id,
                failure_code=FailureCode.CATALOG_UNAVAILABLE,
                message=str(exc),
                retryable=True,
            )


def decision_to_event(decision: ProductIdentityDecision) -> ProductIdentityDecidedEvent:
    requires_human = decision.status != DecisionStatus.ACCEPT
    return ProductIdentityDecidedEvent(
        idempotency_key=f"{decision.rfq_id}:{decision.line_id}:product-identity:v1",
        payload=decision,
        risk=RiskEnvelope(
            level="medium" if requires_human else "low",
            requires_human_approval=requires_human,
        ),
    )


class FakeCatalog:
    def __init__(self, *, unavailable: bool = False) -> None:
        self._unavailable = unavailable
        self._products = [
            ProductRecord(
                product_id="ABB:S203-C16",
                manufacturer="ABB",
                sku="S203-C16",
                name="ABB S203-C16 circuit breaker 3P C16",
                category="circuit_breaker",
                attributes={"poles": "3P", "current": "16A", "curve": "C"},
            ),
            ProductRecord(
                product_id="ABB:S203-C20",
                manufacturer="ABB",
                sku="S203-C20",
                name="ABB S203-C20 circuit breaker 3P C20",
                category="circuit_breaker",
                attributes={"poles": "3P", "current": "20A", "curve": "C"},
            ),
        ]
        self._by_norm = {normalize_mpn(product.sku): product for product in self._products}

    def _check(self) -> None:
        if self._unavailable:
            raise CatalogUnavailable("Catalog dependency unavailable")

    def find_normalized_exact(
        self, *, normalized_mpn: str, manufacturer: str | None
    ) -> ProductRecord | None:
        self._check()
        product = self._by_norm.get(normalized_mpn)
        if product is None or (manufacturer and product.manufacturer != manufacturer):
            return None
        return product

    def retrieve_candidates(
        self, line: NormalizedRFQLine, *, limit: int = 5
    ) -> list[ProductCandidate]:
        self._check()
        if line.category != "circuit_breaker":
            return []
        return [
            ProductCandidate(
                product=product,
                relation=MatchRelation.POSSIBLE_MATCH,
                score=max(0.0, 0.82 - index * 0.08),
                evidence=(
                    EvidenceItem(
                        source="fake_retrieval",
                        key="category",
                        value=product.category,
                    ),
                ),
            )
            for index, product in enumerate(self._products[:limit])
        ]
