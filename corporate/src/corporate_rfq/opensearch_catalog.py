from __future__ import annotations

from typing import Any, Protocol

from pydantic import BaseModel, ConfigDict, Field

from corporate_rfq.models import (
    CatalogUnavailable,
    EvidenceItem,
    MatchRelation,
    NormalizedRFQLine,
    ProductCandidate,
    ProductRecord,
    normalize_mpn,
)


CATALOG_INDEX = "gamm_catalog_products"
_SOURCE_FIELDS = ["id", "sku", "name", "brand", "category", "attributes"]


class OpenSearchAttributeDTO(BaseModel):
    model_config = ConfigDict(frozen=True)

    key: str
    value: str


class OpenSearchProductSourceDTO(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: str | None = None
    sku: str
    name: str
    brand: str
    category: str
    attributes: tuple[OpenSearchAttributeDTO, ...] = ()


class OpenSearchHitDTO(BaseModel):
    model_config = ConfigDict(frozen=True, populate_by_name=True)

    doc_id: str = Field(alias="_id")
    raw_score: float = Field(default=0.0, alias="_score")
    source: OpenSearchProductSourceDTO = Field(alias="_source")


class OpenSearchTransportError(RuntimeError):
    pass


class OpenSearchReadOnlyTransport(Protocol):
    def search(self, *, index: str, body: dict[str, Any]) -> dict[str, Any]: ...


def build_exact_lookup_body(normalized_mpn: str, *, size: int = 5) -> dict[str, Any]:
    return {
        "size": size,
        "_source": _SOURCE_FIELDS,
        "query": {
            "match": {
                "sku": {
                    "query": normalized_mpn,
                }
            }
        },
    }


def build_candidate_body(line: NormalizedRFQLine, *, limit: int = 5) -> dict[str, Any]:
    must: list[dict[str, Any]] = []
    should: list[dict[str, Any]] = []

    if line.part_number_normalized:
        should.append({"match": {"sku": {"query": line.part_number_normalized, "boost": 4.0}}})
    if line.category:
        must.append({"match": {"category": {"query": line.category}}})
    if line.manufacturer:
        must.append({"match": {"brand": {"query": line.manufacturer}}})

    for key, value in sorted(line.attributes.items()):
        must.append(
            {
                "nested": {
                    "path": "attributes",
                    "query": {
                        "bool": {
                            "must": [
                                {"match": {"attributes.key": key}},
                                {"match": {"attributes.value": value}},
                            ]
                        }
                    },
                }
            }
        )

    if not should:
        should.append({"match": {"name": {"query": line.raw_text}}})

    return {
        "size": limit,
        "_source": _SOURCE_FIELDS,
        "query": {
            "bool": {
                "must": must,
                "should": should,
                "minimum_should_match": 1,
            }
        },
    }


class OpenSearchCatalogReadOnlyAdapter:
    """Read-only retrieval adapter for the documented catalog index contract.

    Raw OpenSearch _score is kept as evidence only. It is not treated as a
    probability and therefore is not mapped into ProductCandidate.score.
    """

    def __init__(
        self,
        transport: OpenSearchReadOnlyTransport,
        *,
        index: str = CATALOG_INDEX,
    ) -> None:
        self._transport = transport
        self._index = index

    @staticmethod
    def _parse_hits(response: dict[str, Any]) -> list[OpenSearchHitDTO]:
        hits = response.get("hits", {}).get("hits", [])
        return [OpenSearchHitDTO.model_validate(hit) for hit in hits]

    @staticmethod
    def _to_product(hit: OpenSearchHitDTO) -> ProductRecord:
        source = hit.source
        return ProductRecord(
            product_id=source.id or hit.doc_id,
            manufacturer=source.brand,
            sku=source.sku,
            name=source.name,
            category=source.category,
            attributes={item.key: item.value for item in source.attributes},
        )

    def find_normalized_exact(
        self,
        *,
        normalized_mpn: str,
        manufacturer: str | None,
    ) -> ProductRecord | None:
        try:
            response = self._transport.search(
                index=self._index,
                body=build_exact_lookup_body(normalized_mpn),
            )
        except OpenSearchTransportError as exc:
            raise CatalogUnavailable("OpenSearch catalog read dependency unavailable") from exc

        for hit in self._parse_hits(response):
            product = self._to_product(hit)
            if normalize_mpn(product.sku) != normalized_mpn:
                continue
            if manufacturer is not None and product.manufacturer != manufacturer:
                continue
            return product
        return None

    def retrieve_candidates(
        self,
        line: NormalizedRFQLine,
        *,
        limit: int = 5,
    ) -> list[ProductCandidate]:
        try:
            response = self._transport.search(
                index=self._index,
                body=build_candidate_body(line, limit=limit),
            )
        except OpenSearchTransportError as exc:
            raise CatalogUnavailable("OpenSearch catalog read dependency unavailable") from exc

        candidates: list[ProductCandidate] = []
        for hit in self._parse_hits(response)[:limit]:
            product = self._to_product(hit)
            candidates.append(
                ProductCandidate(
                    product=product,
                    relation=MatchRelation.POSSIBLE_MATCH,
                    score=0.0,
                    evidence=(
                        EvidenceItem(source="opensearch", key="index", value=self._index),
                        EvidenceItem(source="opensearch", key="document_id", value=hit.doc_id),
                        EvidenceItem(
                            source="opensearch",
                            key="raw_score",
                            value=str(hit.raw_score),
                        ),
                    ),
                )
            )
        return candidates
