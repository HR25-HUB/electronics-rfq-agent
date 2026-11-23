# RFQ-MEMORY-001.A1.3 integration gates

Status: EXPERIMENTAL, not production-ready.

## Implemented
- PostgreSQL adapter exposing the existing MemoryRepository operations; schema migration included but **not executed** against PostgreSQL.
- Trusted PIM verification port with independent authorizer; mock PIM only in tests.
- PydanticAI DeepSeek extraction-only adapter, opt-in via RFQ_ALLOW_EXTERNAL_LLM=1; optional InputGuardrail from Pydantic AI Harness.
- Five new offline tests; 14 tests passed locally combined with A1.2.

## Blockers
1. PostgreSQL environment, real connection, migration integration tests and rollback.
2. Real PIM API with service identity, source revocation and evidence freshness.
3. Real DeepSeek test with approved, sanitized requests and locked package versions.
4. Harness API integration test and application policy beyond basic secret redaction.
5. OpenSearch projection and outbox publisher for Redpanda; Prefect workflow.
6. Tenant ACLs at application + DB level; RLS and authoritative verifier permissions.
7. OSS Architecture Gate G1/G2 and verified production release gate G4.

## Windows validation
From `experiments/rfq-memory-a12`:
```powershell
$env:UV_LINK_MODE = "copy"
uv run --python 3.12 --with pytest --with pytest-asyncio python -m pytest -q
```
Do not set RFQ_ALLOW_EXTERNAL_LLM for offline tests.

## Quality and security notes
The fake PIM in tests is synthetic and must never be used as a production source. The PostgreSQL adapter is a starting implementation, not audited for concurrency or authorization. Do not merge this draft PR until independent review and integration verification.
