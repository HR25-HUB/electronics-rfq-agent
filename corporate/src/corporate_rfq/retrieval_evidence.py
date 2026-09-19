from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from typing import Any, Literal, Protocol
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field

from corporate_rfq.opensearch_catalog import (
    OpenSearchReadOnlyTransport,
    OpenSearchTransportError,
)


class OpenSearchReadEvidence(BaseModel):
    model_config = ConfigDict(frozen=True)

    schema_version: str = "1.0.0"
    evidence_id: UUID = Field(default_factory=uuid4)
    trace_id: UUID
    occurred_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    transport: Literal["opensearch-http"] = "opensearch-http"
    operation: Literal["search"] = "search"
    index: str
    query_sha256: str
    outcome: Literal["success", "failure"]
    hit_count: int = Field(ge=0)
    took_ms: int | None = Field(default=None, ge=0)
    timed_out: bool | None = None
    error_class: str | None = None


class RetrievalEvidenceSink(Protocol):
    def record(self, evidence: OpenSearchReadEvidence) -> None: ...


class InMemoryRetrievalEvidenceSink:
    def __init__(self) -> None:
        self.items: list[OpenSearchReadEvidence] = []

    def record(self, evidence: OpenSearchReadEvidence) -> None:
        self.items.append(evidence)


def canonical_query_sha256(body: dict[str, Any]) -> str:
    canonical = json.dumps(
        body,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


class EvidenceRecordingOpenSearchTransport:
    """Decorates a read transport and records non-content audit evidence."""

    def __init__(
        self,
        delegate: OpenSearchReadOnlyTransport,
        sink: RetrievalEvidenceSink,
        *,
        trace_id: UUID | None = None,
    ) -> None:
        self._delegate = delegate
        self._sink = sink
        self._trace_id = trace_id or uuid4()

    def search(self, *, index: str, body: dict[str, Any]) -> dict[str, Any]:
        query_hash = canonical_query_sha256(body)

        try:
            response = self._delegate.search(index=index, body=body)
        except OpenSearchTransportError as exc:
            self._sink.record(
                OpenSearchReadEvidence(
                    trace_id=self._trace_id,
                    index=index,
                    query_sha256=query_hash,
                    outcome="failure",
                    hit_count=0,
                    error_class=type(exc).__name__,
                )
            )
            raise

        hits = response.get("hits", {}).get("hits", [])
        hit_count = len(hits) if isinstance(hits, list) else 0
        took = response.get("took")
        timed_out = response.get("timed_out")

        self._sink.record(
            OpenSearchReadEvidence(
                trace_id=self._trace_id,
                index=index,
                query_sha256=query_hash,
                outcome="success",
                hit_count=hit_count,
                took_ms=took if isinstance(took, int) and took >= 0 else None,
                timed_out=timed_out if isinstance(timed_out, bool) else None,
            )
        )
        return response
