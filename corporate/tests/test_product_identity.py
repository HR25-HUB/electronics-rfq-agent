from corporate_rfq.models import (
    DecisionStatus,
    FailureCode,
    MatchRelation,
    ProductIdentityDecision,
    ProductIdentityFailure,
    RawRFQLine,
)
from corporate_rfq.service import FakeCatalog, ResolveProductIdentity, decision_to_event


def test_normalized_exact_accepts() -> None:
    result = ResolveProductIdentity(FakeCatalog()).execute(
        RawRFQLine(rfq_id="RFQ-001", line_id="1", raw_text="ABB S203 C16 автомат 3п 16А — 10 шт")
    )
    assert isinstance(result, ProductIdentityDecision)
    assert result.status == DecisionStatus.ACCEPT
    assert result.relation == MatchRelation.NORMALIZED_EXACT
    assert result.canonical_product_id == "ABB:S203-C16"


def test_non_exact_candidate_never_auto_accepts() -> None:
    result = ResolveProductIdentity(FakeCatalog()).execute(
        RawRFQLine(rfq_id="RFQ-002", line_id="1", raw_text="ABB автомат трехполюсный 16А — 5 шт")
    )
    assert isinstance(result, ProductIdentityDecision)
    assert result.status == DecisionStatus.REVIEW_REQUIRED
    assert result.canonical_product_id is None
    assert result.candidates


def test_catalog_outage_is_not_not_found() -> None:
    result = ResolveProductIdentity(FakeCatalog(unavailable=True)).execute(
        RawRFQLine(rfq_id="RFQ-003", line_id="1", raw_text="ABB S203 C16 автомат 3п 16А — 10 шт")
    )
    assert isinstance(result, ProductIdentityFailure)
    assert result.failure_code == FailureCode.CATALOG_UNAVAILABLE
    assert result.retryable is True


def test_ambiguous_quantity_never_defaults_to_one() -> None:
    result = ResolveProductIdentity(FakeCatalog()).execute(
        RawRFQLine(rfq_id="RFQ-004", line_id="1", raw_text="ABB S203 C16 автомат 3п 16А")
    )
    assert isinstance(result, ProductIdentityFailure)
    assert result.failure_code == FailureCode.AMBIGUOUS_QUANTITY


def test_review_event_requires_human_approval() -> None:
    result = ResolveProductIdentity(FakeCatalog()).execute(
        RawRFQLine(rfq_id="RFQ-005", line_id="1", raw_text="ABB автомат трехполюсный 16А — 5 шт")
    )
    assert isinstance(result, ProductIdentityDecision)
    event = decision_to_event(result)
    assert event.schema_version == "1.0.0"
    assert event.risk.requires_human_approval is True
    assert event.idempotency_key == "RFQ-005:1:product-identity:v1"
