from __future__ import annotations

from typing import Any
from uuid import uuid4

import httpx
from pydantic import BaseModel, ConfigDict

from corporate_rfq.models import ProductIdentityDecision, ProductIdentityFailure, RawRFQLine
from corporate_rfq.opensearch_catalog import CATALOG_INDEX, OpenSearchCatalogReadOnlyAdapter
from corporate_rfq.opensearch_http import OpenSearchHttpReadOnlyTransport
from corporate_rfq.retrieval_evidence import (
    EvidenceRecordingOpenSearchTransport,
    InMemoryRetrievalEvidenceSink,
    OpenSearchReadEvidence,
)
from corporate_rfq.service import ResolveProductIdentity


class LiveProbeSummary(BaseModel):
    model_config = ConfigDict(frozen=True)

    trace_id: str
    outcome_kind: str
    decision_status: str | None = None
    relation: str | None = None
    canonical_product_id: str | None = None
    failure_code: str | None = None
    retryable: bool | None = None
    evidence: tuple[OpenSearchReadEvidence, ...]


def run_live_probe(
    *,
    client: httpx.Client,
    raw_line: str,
    index: str = CATALOG_INDEX,
) -> LiveProbeSummary:
    if index != CATALOG_INDEX:
        raise ValueError(f"Live probe is restricted to index {CATALOG_INDEX!r}")

    trace_id = uuid4()
    sink = InMemoryRetrievalEvidenceSink()
    http_transport = OpenSearchHttpReadOnlyTransport(client)
    recording_transport = EvidenceRecordingOpenSearchTransport(
        http_transport,
        sink,
        trace_id=trace_id,
    )
    catalog = OpenSearchCatalogReadOnlyAdapter(recording_transport, index=index)
    result = ResolveProductIdentity(catalog).execute(
        RawRFQLine(
            rfq_id="LIVE-PROBE",
            line_id="1",
            raw_text=raw_line,
        )
    )

    if isinstance(result, ProductIdentityDecision):
        return LiveProbeSummary(
            trace_id=str(trace_id),
            outcome_kind="decision",
            decision_status=result.status.value,
            relation=result.relation.value,
            canonical_product_id=result.canonical_product_id,
            evidence=tuple(sink.items),
        )

    assert isinstance(result, ProductIdentityFailure)
    return LiveProbeSummary(
        trace_id=str(trace_id),
        outcome_kind="failure",
        failure_code=result.failure_code.value,
        retryable=result.retryable,
        evidence=tuple(sink.items),
    )


def redacted_probe_output(summary: LiveProbeSummary) -> dict[str, Any]:
    """Return an output payload that intentionally excludes RFQ text and credentials."""

    return summary.model_dump(mode="json")
