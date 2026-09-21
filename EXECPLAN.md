# EXECPLAN — RPO-001

## Goal

Prove the procurement-side canonical domain slice:

```text
One RFQ line
→ three supplier quotes
→ evidence-backed comparison
→ human AwardDecision
```

## Task Contract

### Scope

Add only:

- Pydantic v2 procurement-domain contracts;
- explicit Supplier RFQ state transitions and guards;
- deterministic candidate eligibility policy;
- Golden-4 tests.

### Non-goals

- UI / Next.js;
- Saleor writes;
- 1C integration;
- supplier portal;
- email delivery;
- Redpanda / Prefect;
- persistence/repositories;
- refactoring existing `QuoteAgent`, `Quote`, parser or ERP adapters;
- unrelated dependency upgrades.

### Affected components

```text
src/electronics_rfq_agent/procurement/
tests/golden/procurement/
```

### Acceptance criteria

1. Existing public sales-quotation API remains unchanged.
2. Procurement contracts use Pydantic v2.
3. Monetary and quantity values use `Decimal`.
4. `SupplierQuoteLine` explicitly references `SupplierRFQLine`.
5. Decision-driving facts can carry source provenance.
6. Quote facts, derived comparison and human award remain separate models.
7. Invalid Supplier RFQ transitions are rejected.
8. Golden-4:
   - G-001 exact match → ELIGIBLE;
   - G-002 substitute → REVIEW_REQUIRED;
   - G-003 MOQ mismatch → REVIEW_REQUIRED;
   - G-004 conflicting evidence → REVIEW_REQUIRED.
9. No automatic award path exists.

### Constraints

- additive, small diff;
- Python 3.10 compatible;
- no breaking changes;
- no hidden LLM decision;
- no production side effects.

## Files/components

```text
src/electronics_rfq_agent/procurement/__init__.py
src/electronics_rfq_agent/procurement/domain/__init__.py
src/electronics_rfq_agent/procurement/domain/models.py
src/electronics_rfq_agent/procurement/domain/state_machine.py
src/electronics_rfq_agent/procurement/domain/policy.py
tests/golden/procurement/test_golden_procurement.py
```

## Implementation steps

1. Define immutable procurement contracts.
2. Add provenance validation.
3. Add explicit state transition map.
4. Add deterministic eligibility policy.
5. Add Golden-4 tests.
6. Run repository validation gates.
7. Record execution evidence.
8. Reviewer attempts to break invariants before PR.

## Validation

```bash
uv run ruff check .
uv run ruff format --check .
uv run mypy src/ --strict
uv run pytest tests/
uv run pytest tests/golden/procurement -q
```

## Risks

- accidental coupling to existing customer `Quote`;
- invalid Decimal/JSON boundary;
- evidence accepted without stable provenance;
- substitute or MOQ mismatch silently treated as eligible;
- state transition bypass.

## Rollback

The implementation is additive under `procurement/`. Rollback is deletion of the new package and Golden tests; existing APIs are untouched.

## Promotion gate

Do not merge until:

- all validation gates pass;
- Golden-4 pass;
- reviewer confirms no implicit supplier-award path;
- human approval is explicit.
