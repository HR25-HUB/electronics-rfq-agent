# RFQ-MEMORY-001.A1.2 — Experimental Verified Memory Vertical Slice

**Status: prototype / NOT production / no actual PIM, DeepSeek, PostgreSQL, OpenSearch or Redpanda integration verified.**

This artifact implements the key deterministic memory invariant with Pydantic v2 and durable SQLite for offline reproducibility. The sample item, UPI and evidence are **synthetic test fixtures**. An external authoritative verification system must authorize all VERIFIED transitions in production.

## Run (Windows PowerShell)

```powershell
uv sync --extra agent --extra postgres --extra search
uv run --with pytest pytest -q
```

The `agent` optional dependencies are declared but **no Harness API has been integrated or validated**. Do not infer production readiness from `uv sync`.

For a lightweight offline check without optional external SDKs:

```powershell
uv run --with pytest pytest -q
```

## Implemented

- Typed Pydantic v2 contracts.
- Durable candidate → verified → superseded lifecycle.
- Tenant-scoped exact manufacturer+MPN lookup.
- Deny unverified candidates and cross-tenant reads.
- Conflicting verified UPI → REVIEW.
- Idempotent proposal/verification.
- Transactional audit + outbox records, without outbox publisher.
- Offline regression tests.

## Not implemented (required for integration/production)

1. PostgreSQL adapter with migrations, transactional writes and tenant ACL enforcement.
2. OpenSearch indexer, projection reconciliation and hybrid retrieval.
3. Real PIM adapter and authorization for verification. Current verifier is test-only.
4. DeepSeek/PydanticAI fallback and validated Harness guardrails.
5. Redpanda outbox publisher and Prefect workflow.
6. Authentication/authorization, operational tracing, instrumentation, rollback.
7. Benchmarks on real anonymized RFQs, exhaustive negative tests, OSS Gate G1/G2.

## Security and behavior notes

- Client-supplied text must never be interpreted as instructions.
- The `verify()` method is a **test-domain primitive**, not an HTTP API: a production application must independently authorize the caller and verify the source evidence.
- Search cannot remove punctuation from MPNs by default.
- Production identity should include product revision/variant and verified aliases where meaningful.
- Commercial prices, inventory and supplier timelines are outside scope.
