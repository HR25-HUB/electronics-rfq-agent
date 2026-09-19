from __future__ import annotations

from typing import Protocol, runtime_checkable

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


class CatalogAppProductDTO(BaseModel):
    """Canonical read model expected from the Catalog.App boundary.

    This is an internal adapter contract, not a claim about the current
    Catalog.App HTTP/GraphQL payload. The concrete transport must map the
    real external schema into this DTO.
    """

    model_config = ConfigDict(frozen=True)

    product_id: str = Field(min_length=1)
    manufacturer: str = Field(min_length=1)
    sku: str = Field(min_length=1)
    name: str = Field(min_length=1)
    category: str = Field(min_length=1)
    attributes: dict[str, str] = Field(default_factory=dict)
    source_revision: str | None = None


class CatalogAppCandidateDTO(BaseModel):
    model_config = ConfigDict(frozen=True)

    product: CatalogAppProductDTO
    score: float = Field(ge=0.0, le=1.0)
    matched_by: str = Field(min_length=1)


class CatalogAppTransportError(RuntimeError):
    """Transport-level error before domain translation."""


@runtime_checkable
class CatalogAppReadOnlyTransport(Protocol):
    """Minimal read-only surface required from a concrete Catalog.App client."""

    def get_by_normalized_mpn(self, normalized_mpn: str) -> CatalogAppProductDTO | None: ...

    def search_candidates(
        self,
        *,
        manufacturer: str | None,
        normalized_mpn: str | None,
        category: str | None,
        attributes: dict[str, str],
        limit: int,
    ) -> list[CatalogAppCandidateDTO]: ...


class CatalogAppReadOnlyAdapter:
    """Maps a read-only Catalog.App transport to the Product Identity CatalogPort."""

    def __init__(self, transport: CatalogAppReadOnlyTransport) -> None:
        self._transport = transport

    @staticmethod
    def _to_product(dto: CatalogAppProductDTO) -> ProductRecord:
        return ProductRecord(
            product_id=dto.product_id,
            manufacturer=dto.manufacturer,
            sku=dto.sku,
            name=dto.name,
            category=dto.category,
            attributes=dto.attributes,
        )

    def find_normalized_exact(
        self,
        *,
        normalized_mpn: str,
        manufacturer: str | None,
    ) -> ProductRecord | None:
        try:
            dto = self._transport.get_by_normalized_mpn(normalized_mpn)
        except CatalogAppTransportError as exc:
            raise CatalogUnavailable("Catalog.App read dependency unavailable") from exc

        if dto is None:
            return None

        if normalize_mpn(dto.sku) != normalized_mpn:
            return None

        if manufacturer is not None and dto.manufacturer != manufacturer:
            return None

        return self._to_product(dto)

    def retrieve_candidates(
        self,
        line: NormalizedRFQLine,
        *,
        limit: int = 5,
    ) -> list[ProductCandidate]:
        try:
            candidates = self._transport.search_candidates(
                manufacturer=line.manufacturer,
                normalized_mpn=line.part_number_normalized,
                category=line.category,
                attributes=line.attributes,
                limit=limit,
            )
        except CatalogAppTransportError as exc:
            raise CatalogUnavailable("Catalog.App read dependency unavailable") from exc

        return [
            ProductCandidate(
                product=self._to_product(candidate.product),
                relation=MatchRelation.POSSIBLE_MATCH,
                score=candidate.score,
                evidence=(
                    EvidenceItem(
                        source="catalog.app",
                        key="matched_by",
                        value=candidate.matched_by,
                    ),
                    EvidenceItem(
                        source="catalog.app",
                        key="canonical_sku",
                        value=candidate.product.sku,
                    ),
                ),
            )
            for candidate in candidates[:limit]
        ]
