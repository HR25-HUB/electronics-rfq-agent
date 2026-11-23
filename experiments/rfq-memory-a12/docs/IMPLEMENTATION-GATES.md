# RFQ-MEMORY-001.A1.2 — Implementation / Acceptance gates

- G0 problem scoped: verified memory for reusable product identity, not pricing.
- G1 OSS research: **OPEN** (5 alternatives / 2 deep reviews / license and maintenance checks).
- G2 architecture decision: **OPEN** (PostgreSQL/OpenSearch proposal has not received sign-off).
- G3 prototype: **PARTIAL** (offline memory domain implemented; PydanticAI/Harness are not called).
- G4 production: **BLOCKED** (unverified integrations and authorization).

## Required next implementation issue

`RFQ-MEMORY-001.A1.3 — PostgreSQL Port + PIM Verification + Agent Fallback + Integration Gate`

**Sequence:** 1) verified PostgreSQL + migration; 2) test evidence provenance and caller authentication; 3) OpenSearch projection/index; 4) DeepSeek PydanticAI adapter; 5) validated selective Harness; 6) Prefect/Redpanda outbox; 7) non-synthetic RFQ evaluation and approval.

**Stop conditions:** cross-tenant leak, false verified UPI reuse, LLM self-verification, unbounded retries, lost audit events.

## Portability

Domain uses `MemoryRepository` protocol; SQLite is an offline adapter only. Do not replace without port-level contract tests.
