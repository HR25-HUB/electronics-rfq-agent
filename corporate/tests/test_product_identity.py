# ruff: noqa: RUF001
from corporate_rfq.models import (
    DecisionStatus,
    FailureCode,
    MatchRelation,
    ProductIdentityDecision,
    ProductIdentityFailure,
    RawRFQLine,
)
from corporate_rfq.service import FakeCatalog, ResolveProductIdentity, decision_to_event


def resolve(text: str) -> ProductIdentityDecision | ProductIdentityFailure:
    return ResolveProductIdentity(FakeCatalog()).execute(
        RawRFQLine(rfq_id="RFQ-TEST", line_id="1", raw_text=text)
    )


def test_normalized_exact_accepts() -> None:
    result = resolve("ABB S203 C16 автомат 3п 16А — 10 шт")
    assert isinstance(result, ProductIdentityDecision)
    assert result.status == DecisionStatus.ACCEPT
    assert result.relation == MatchRelation.NORMALIZED_EXACT
    assert result.canonical_product_id == "ABB:S203-C16"


def test_non_exact_candidate_never_auto_accepts() -> None:
    result = resolve("ABB автомат трехполюсный 16А — 5 шт")
    assert isinstance(result, ProductIdentityDecision)
    assert result.status == DecisionStatus.REVIEW_REQUIRED
    assert result.canonical_product_id is None
    assert result.candidates


def test_catalog_outage_is_not_not_found() -> None:
    result = ResolveProductIdentity(FakeCatalog(unavailable=True)).execute(
        RawRFQLine(
            rfq_id="RFQ-003",
            line_id="1",
            raw_text="ABB S203 C16 автомат 3п 16А — 10 шт",
        )
    )
    assert isinstance(result, ProductIdentityFailure)
    assert result.failure_code == FailureCode.CATALOG_UNAVAILABLE
    assert result.retryable is True


def test_ambiguous_quantity_never_defaults_to_one() -> None:
    result = resolve("ABB S203 C16 автомат 3п 16А")
    assert isinstance(result, ProductIdentityFailure)
    assert result.failure_code == FailureCode.AMBIGUOUS_QUANTITY


def test_review_event_requires_human_approval() -> None:
    result = resolve("ABB автомат трехполюсный 16А — 5 шт")
    assert isinstance(result, ProductIdentityDecision)
    event = decision_to_event(result)
    assert event.schema_version == "1.0.0"
    assert event.risk.requires_human_approval is True
    assert event.idempotency_key == "RFQ-TEST:1:product-identity:v1"


def test_exact_mpn_with_pole_conflict_is_rejected() -> None:
    result = resolve("ABB S203 C16 автомат 1п 16А — 10 шт")
    assert isinstance(result, ProductIdentityDecision)
    assert result.status == DecisionStatus.REJECT
    assert result.canonical_product_id is None
    assert any("poles" in item.key for item in result.evidence)


def test_exact_mpn_with_current_conflict_is_rejected() -> None:
    result = resolve("ABB S203 C16 автомат 3п 20А — 10 шт")
    assert isinstance(result, ProductIdentityDecision)
    assert result.status == DecisionStatus.REJECT
    assert result.canonical_product_id is None
    assert any("current" in item.key for item in result.evidence)


def test_exact_mpn_without_manufacturer_requires_review() -> None:
    result = resolve("S203-C16 автомат 3п 16А — 10 шт")
    assert isinstance(result, ProductIdentityDecision)
    assert result.status == DecisionStatus.REVIEW_REQUIRED
    assert result.canonical_product_id is None
    assert "manufacturer is not proven" in result.policy_reasons


def test_analogue_intent_blocks_exact_auto_accept() -> None:
    result = resolve("ABB S203-C16 или эквивалент Schneider, 3P 16A — 10 pcs")
    assert isinstance(result, ProductIdentityDecision)
    assert result.status == DecisionStatus.REVIEW_REQUIRED
    assert result.canonical_product_id is None
    assert any("analogue/replacement" in reason for reason in result.policy_reasons)


def test_low_confidence_evidence_blocks_exact_auto_accept() -> None:
    result = resolve("ABB S203-C16? OCR confidence low, 3п 16А — 10 шт")
    assert isinstance(result, ProductIdentityDecision)
    assert result.status == DecisionStatus.REVIEW_REQUIRED
    assert result.canonical_product_id is None
    assert any("low-confidence" in reason for reason in result.policy_reasons)


def test_pack_multiplication_requires_explicit_normalization() -> None:
    result = resolve("ABB S203-C16 автомат 3п 16А — 1 pack x 12 pcs")
    assert isinstance(result, ProductIdentityFailure)
    assert result.failure_code == FailureCode.AMBIGUOUS_QUANTITY


def test_negative_quantity_is_failure() -> None:
    result = resolve("ABB S203-C16 автомат 3п 16А — -5 pcs")
    assert isinstance(result, ProductIdentityFailure)
    assert result.failure_code == FailureCode.AMBIGUOUS_QUANTITY
