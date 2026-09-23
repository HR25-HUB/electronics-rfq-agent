# Roadmap

## Milestone 1 — Local deterministic vertical slice
Status: implemented in this branch.

- qualification
- resource budget
- next best question
- objection policy
- KT37/KT38 gates
- deterministic follow-up
- idempotent in-memory order service
- FastAPI + CLI + tests

## Milestone 2 — Durable persistence

- PostgreSQL
- inbox/outbox
- durable order idempotency
- audit/event tables
- migrations

## Milestone 3 — Real adapters

- Bitrix24 inbound events and timeline/tasks
- Saleor GraphQL schema probe
- Saleor quote/order repository
- async 1C registration

## Milestone 4 — Durable workflow

- Temporal workflow for KT36→KT37 waits/timers
- retry/DLQ
- reconciliation

## Milestone 5 — AI shadow mode

- prequalification extraction
- customer-intent extraction
- evidence spans
- model/prompt version
- no execution authority

## Milestone 6 — QUAL20 / Real-5 pilot

Measure conversion, cycle time, GP/hour and policy correctness.
