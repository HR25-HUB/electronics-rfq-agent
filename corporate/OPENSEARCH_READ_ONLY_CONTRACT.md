# OpenSearch Read-Only Retrieval Contract

## Source basis

The project research explicitly describes the product index:

`gamm_catalog_products`

with fields:

- `sku`
- `name`
- `brand`
- `category`
- nested `attributes`
- `product_description_vector`

It also describes an n-gram SKU analyzer and read-only search that consumes OpenSearch hits from `response["hits"]["hits"]`.

This slice implements only that supported retrieval boundary.

## Boundary

```
RFQ Product Identity
        ↓
CatalogPort
        ↓
OpenSearchCatalogReadOnlyAdapter
        ↓
OpenSearchReadOnlyTransport.search(...)
        ↓
gamm_catalog_products
```

## Safety rules

1. The adapter exposes search only. No index/update/delete/bulk operation exists.
2. Exact Product Identity is decided only after normalizing and comparing the returned SKU.
3. Manufacturer mismatch blocks exact resolution.
4. OpenSearch `_score` is preserved as evidence only.
5. Raw `_score` is **not** treated as probability or confidence.
6. Transport failures become `CatalogUnavailable`, never `NOT_FOUND`.

## Query contract

The candidate query may use:

- SKU match
- brand constraint
- category constraint
- nested attribute constraints

The concrete production transport is still separate from this contract and may evolve with the actual OpenSearch deployment.

## Current evidence

Tests validate:

- documented index name;
- documented source fields;
- normalized exact SKU validation;
- nested attribute query construction;
- raw score evidence;
- transport failure translation;
- read-only public surface;
- no regression of Golden RFQ 100.

## Not yet proven

This slice does not prove:

- production OpenSearch connectivity;
- analyzer settings in the live cluster;
- relevance quality;
- Top-1 / Top-3 recall;
- actual Catalog.App → OpenSearch synchronization freshness.

Those require live/read-only infrastructure evidence.
