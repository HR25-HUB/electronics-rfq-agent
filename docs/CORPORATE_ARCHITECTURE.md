# Corporate Architecture

## Context

Actors:
- Customer / RFQ sender
- Sales / Product Manager
- Procurement
- Development/SRE

Systems:
- electronics-rfq-agent OSS core
- Corporate Product Identity layer
- Catalog.App/PIM
- OpenSearch
- Saleor
- 1C KA 2.5
- Bitrix24
- future Redpanda/Prefect runtime

## Current container view

```text
RFQLine
  ↓
Normalizer
  ↓
ResolveProductIdentity
  ↓ CatalogPort
  ├─ FakeCatalog
  ├─ CatalogAppReadOnlyAdapter
  └─ OpenSearchCatalogReadOnlyAdapter
       ↓
       EvidenceRecordingOpenSearchTransport
       ↓
       OpenSearchHttpReadOnlyTransport
```

## Domain invariants

- Candidate != Decision.
- Analogue != exact Product Identity.
- Ambiguous quantity never defaults to 1.
- Technical failure != NOT_FOUND.
- Non-exact candidate never auto-accepts.
- Critical attribute conflict blocks acceptance.
- Production retrieval is read-only at this stage.

## Event contract

ProductIdentityDecidedEvent contains:
- schema_version
- event_id
- event_type
- occurred_at
- producer
- trace_id
- idempotency_key
- payload
- risk envelope

## Roadmap

1. Product Identity safety/evidence — implemented.
2. Real redacted dataset + live read-only retrieval.
3. Sourcing / supplier quote.
4. Pricing / margin policy.
5. Saleor proposal integration.
6. Controlled Redpanda/Prefect orchestration.
