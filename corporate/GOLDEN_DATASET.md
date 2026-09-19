# Golden RFQ Dataset Contract

## Purpose

This harness measures Product Identity behavior against versioned expected outcomes.

Two synthetic datasets are committed:

- `tests/golden/seed.jsonl` — small harness sanity set.
- `tests/golden/golden100-adversarial.jsonl` — 100-case adversarial hypothesis test.

Both are **synthetic only**. They validate safety policy, evaluator behavior, metrics and CI wiring. They are not production-quality evidence and must never be presented as real RFQ accuracy.

## Golden RFQ 100 adversarial design

Version: `synthetic-adversarial-v1.0`.

Ground-truth distribution:

- 15 `ACCEPT`
- 50 `REVIEW_REQUIRED`
- 20 `REJECT`
- 15 `FAILURE`

Strata:

- 15 valid exact identities with formatting/language noise
- 15 exact-looking MPNs without a trusted manufacturer
- 20 OCR/typing/confusable-character MPN corruptions
- 20 exact MPNs with critical attribute conflicts
- 15 quantity/UOM ambiguity cases
- 15 semantic/analogue/other-manufacturer cases

The dataset is deliberately harder than the current implementation. Ground truth is defined independently of current resolver behavior.

## Working hypothesis

The first hypothesis is **safety**, not maximum automation:

> The resolver may miss or defer difficult cases, but it must not auto-ACCEPT a wrong or insufficiently evidenced Product Identity.

### Hard safety gate

`unsafe_auto_substitution_count = 0`

A low case pass rate is evidence for further engineering. An unsafe auto-accept is a release blocker.

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

## Real dataset next step

A later dataset must contain 50–100 **real redacted** RFQ lines under controlled access. Do not place customer names, emails, prices, phone numbers, addresses, or other confidential identifiers into this public repository.

Only the real-redacted dataset can establish a production business baseline for extraction, retrieval precision/recall and manual-review rate.
