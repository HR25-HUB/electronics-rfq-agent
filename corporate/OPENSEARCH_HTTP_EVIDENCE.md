# OpenSearch HTTP Read-Only Transport + EvidencePack

## Purpose

This slice turns the OpenSearch retrieval contract into an executable HTTP transport while preserving the existing safety boundary.

It still does **not** connect CI to the corporate OpenSearch deployment.

## Composition

The transport receives an already-configured `httpx.Client`:

```
httpx.Client(
    base_url=<external configuration>,
    headers=<external configuration>,
    verify=<external configuration>,
)
        ↓
OpenSearchHttpReadOnlyTransport
        ↓
EvidenceRecordingOpenSearchTransport
        ↓
OpenSearchCatalogReadOnlyAdapter
        ↓
Product Identity
```

Base URL, TLS policy and authentication remain outside the domain/adapter code because the repository does not contain authoritative production connection details.

## HTTP restriction

The transport exposes only:

`POST /{index}/_search`

Index names are validated before path construction.

There is no implementation for:

- bulk
- index/create
- update
- delete
- scripts
- mutations

## Retrieval EvidencePack

Each search records content-minimizing evidence:

- schema_version
- evidence_id
- trace_id
- occurred_at
- transport
- operation
- index
- SHA-256 of canonical query JSON
- success/failure outcome
- hit_count
- OpenSearch `took` when available
- `timed_out` when available
- error class on failure

The evidence record deliberately does **not** copy the RFQ query body or OpenSearch response content.

## Next live step

`RFQ-SEARCH-001.1B — One Authorized Live Read → EvidencePack`

Required runtime inputs:

- read-only OpenSearch base URL;
- approved TLS settings;
- approved authentication injected into the httpx client;
- one redacted RFQ line;
- confirmation that the target index is `gamm_catalog_products`.

No production write credential is required or expected.
