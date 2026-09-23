# AGENTS.md

## Business invariants

- Never infer approval from silence.
- Never mutate a dispatched quote; create a new quote version.
- AI never authorizes price, discount, payment terms, product substitution, KT37 or KT38.
- KT37 requires explicit customer evidence tied to the accepted quote version.
- KT38 must match accepted quote version, quantity, unit price and currency.
- 1C is downstream registration and cannot block KT38.
- COLD_CALCULATION changes resource budget, not customer eligibility.
- Every significant transition must be reconstructable by line_id.

## Engineering rules

- Python 3.12+, Pydantic contracts.
- DDD + Hexagonal Architecture.
- Domain imports no FastAPI/vendor clients.
- Deterministic business policy in application layer.
- External I/O only in adapters/API.
- Policy change => regression test.
- Prefer REVIEW_REQUIRED to unsafe inference.
