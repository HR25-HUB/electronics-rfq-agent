# Catalog.App Read-Only Contract Harness

## Purpose

This slice defines the minimum Product Identity boundary required from Catalog.App without inventing the real Catalog.App API.

The repository currently does **not** contain an authoritative Catalog.App HTTP/GraphQL contract. Therefore this slice intentionally stops at a canonical adapter contract.

## Boundary

```
Product Identity application
        ↓
CatalogPort
        ↓
CatalogAppReadOnlyAdapter
        ↓
CatalogAppReadOnlyTransport
        ↓
future concrete HTTP/GraphQL client
        ↓
Catalog.App
```

## Read-only operations

The canonical transport exposes only:

- `get_by_normalized_mpn(...)`
- `search_candidates(...)`

No create/update/delete/upsert/write method is part of the boundary.

## Canonical DTO

A concrete Catalog.App client must map the real external schema into:

- product_id
- manufacturer
- sku
- name
- category
- attributes
- optional source_revision

The DTO is an internal anti-corruption layer. It is **not** documentation of the real Catalog.App payload.

## Reliability

Transport failures are translated to:

```
CatalogUnavailable
```

They must never be converted to `NOT_FOUND`.

## Evidence

Candidate evidence records:

- source = `catalog.app`
- matched_by
- canonical_sku

A future real adapter should add source revision/document/version identifiers whenever Catalog.App can provide them.

## Current validation

This slice uses local canonical fixtures only. It proves:

- adapter/domain mapping;
- manufacturer mismatch handling;
- candidate evidence propagation;
- result limiting;
- technical failure translation;
- absence of write methods on the public adapter surface.

It does **not** prove connectivity to the real Catalog.App deployment.

## Next step

Provide one authoritative Catalog.App read contract or a redacted real response sample, then implement:

`RFQ-PIM-001.1 — One Real Read-Only Catalog.App Call → ProductRecord Evidence`
