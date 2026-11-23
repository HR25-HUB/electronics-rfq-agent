# RFQ-MEMORY-001.A1.4 — Real PostgreSQL integration

**Status: test suite ready; actual PostgreSQL integration NOT yet verified.**

## Problem fixed
The A1.3 implementation first selected an existing audit row before inserting. Concurrent replay could produce duplicate audit/outbox events. Migration 002 adds a unique index on (memory_id, action); the adapter now inserts an audit row with ON CONFLICT DO NOTHING RETURNING, creating its outbox event only if a new audit row was inserted. The application transaction spans memory write + audit + outbox.

## Isolation
- PostgreSQL 16 disposable test instance only; 127.0.0.1:55432.
- DSN guard requires local host and exactly the database name rfq_memory_test.
- Integration test creates a new disposable schema for every case and deletes only that schema.
- No customer/production RFQs; fixture identifiers and PIM evidence are synthetic.
- No Redpanda publisher is built here; only transactional outbox database writes are checked.

## Windows PowerShell quickstart
Run inside experiments/rfq-memory-a12:

```powershell
$env:UV_LINK_MODE = 'copy'
$env:RFQ_TEST_DB_PASSWORD = 'a-local-test-password-only'
docker compose -f compose.postgres-test.yml up -d --wait
$env:RFQ_TEST_POSTGRES_DSN = "postgresql://rfq_test:$($env:RFQ_TEST_DB_PASSWORD)@127.0.0.1:55432/rfq_memory_test"
$env:RFQ_REQUIRE_POSTGRES = '1'
uv run --python 3.12 --with pytest --with pytest-asyncio --with 'psycopg[binary]' python -m pytest -q
docker compose -f compose.postgres-test.yml down
```

Only use a throwaway local test password; URL-encode special characters if used. Docker data is tmpfs and discarded on container termination. Do not bypass Windows App Control if it blocks a binary.

## Mandatory integration tests
- PG01 durable verified state across PostgreSQL connections.
- PG02 replay leaves one audit and outbox per memory business action.
- PG03 conflict of two verified UPIs requires REVIEW; tenant isolation.
- PG04 failed outbox proposal rolls back memory and audit.
- PG05 failed outbox verification rolls back status transition.
- PG06 eight concurrent duplicate proposals create one record and one event.
- PG07 revoked records are not reused; repeated revocation idempotent.

## Gate status
G1/G2 OSS and architecture approval: OPEN. G4 production gate: BLOCKED.
No verification yet of actual PostgreSQL execution in the local environment; 7 integration tests skipped and 14 offline tests passed. GitHub workflow requires live PostgreSQL: missing DSN or driver is a failure, never a silent pass.

Not covered: production RLS, authorization of verifier, real PIM, PydanticAI/DeepSeek/Harness runtime, OpenSearch, Redpanda delivery, Prefect or deployment rollback.
