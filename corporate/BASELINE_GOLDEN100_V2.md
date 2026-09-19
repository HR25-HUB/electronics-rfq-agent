# Golden RFQ 100 — Baseline v2

Dataset: `synthetic-adversarial-v1.0`

Dataset blob SHA: `e26cdab5fd40e8b741566f3a0ba4607d393c5cbb`

Compared with Baseline v1: **dataset unchanged**.

## Purpose

Verify the remediation slice:

`RFQ-SAFE-001.2 — Golden 100 Unsafe 21 → Zero Unsafe Auto-Accepts`

The benchmark remains synthetic adversarial evidence. It is not production RFQ accuracy evidence.

## Baseline comparison

| Metric | Baseline v1 | Baseline v2 |
|---|---:|---:|
| total_cases | 100 | 100 |
| passed_cases | 79 | 100 |
| case_pass_rate | 0.79 | 1.00 |
| accepted_count | 36 | 15 |
| review_required_count | 31 | 50 |
| rejected_count | 20 | 20 |
| failure_count | 13 | 15 |
| manual_review_rate | 0.31 | 0.50 |
| exact_match_precision | 0.4167 | 1.00 |
| unsafe_auto_substitution_count | 21 | 0 |

## What changed

The Product Identity resolver now blocks automatic exact acceptance when any of the following is true:

1. manufacturer is not proven;
2. analogue/replacement intent is present;
3. low-confidence source evidence is present;
4. quantity/UOM is ambiguous;
5. pack multiplication requires interpretation;
6. critical product attributes conflict with catalog evidence.

## Evidence

GitHub Actions Corporate RFQ CI passed:

- ruff format: PASS
- ruff lint: PASS
- pyrefly: PASS
- pytest: PASS
- Golden seed evaluation: PASS
- Golden RFQ 100 adversarial evaluation: PASS

Golden RFQ 100 result:

- ACCEPT: 15
- REVIEW_REQUIRED: 50
- REJECT: 20
- FAILURE: 15
- exact_match_precision: 1.0
- unsafe_auto_substitution_count: 0

## Interpretation

The safety hypothesis is now supported on this synthetic adversarial dataset:

> Difficult or insufficiently evidenced RFQ lines are deferred or rejected rather than incorrectly auto-accepted.

This does **not** prove production accuracy. The next evidence stage must use real, redacted RFQ lines and a real Catalog.App/OpenSearch retrieval path.

## Next slice

`RFQ-EVIDENCE-001.1 — Real Redacted RFQ Set → Catalog.App Read-Only Baseline`

Exit criteria:

- real redacted dataset under controlled access;
- no customer-identifying data in the public repository;
- immutable dataset version;
- Product Identity decisions produced from real Catalog.App evidence;
- unsafe_auto_substitution_count = 0;
- retrieval precision/recall and manual-review rate measured.
