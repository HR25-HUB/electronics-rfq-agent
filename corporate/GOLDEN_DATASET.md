# Golden RFQ Dataset Contract

## Purpose

This harness measures Product Identity behavior against versioned expected outcomes.

The committed `tests/golden/seed.jsonl` file is **synthetic only**. It validates the evaluator, metrics and CI wiring. It is not production-quality evidence and must never be presented as a real RFQ benchmark.

## JSONL contract

Each line is one independent case with:

- `case_id`
- `dataset_version`
- `source_kind`: `synthetic` or `real_redacted`
- immutable `rfq_id` / `line_id`
- original or redacted `raw_text`
- expected outcome
- optional tags

Decision cases define `expected_status` and, for `ACCEPT`, `expected_product_id`.
Failure cases define `expected_failure_code`.

A dataset file must contain exactly one `dataset_version` and unique case IDs.

## Metrics

The evaluator emits:

- total cases
- case pass rate
- accepted count
- review-required count
- rejected count
- failure count
- manual review rate
- exact-match precision
- unsafe auto-substitution count

### Hard safety gate

`unsafe_auto_substitution_count = 0`

This gate is enforced even before business-quality thresholds are calibrated.

## Real dataset next step

Create a separate, access-controlled, redacted dataset with 50–100 real RFQ lines. Do not put customer names, emails, prices, phone numbers, addresses, or other confidential identifiers into this public repository.

Suggested strata:

- exact MPN
- punctuation/spacing variants
- typo in MPN
- missing manufacturer
- Cyrillic/Latin mixtures
- description without MPN
- ambiguous candidate set
- obsolete SKU
- analogue request
- wrong/missing quantity
- conflicting critical attributes
- no match

Only the real-redacted dataset can establish a business baseline for retrieval precision/recall and manual-review rate.
