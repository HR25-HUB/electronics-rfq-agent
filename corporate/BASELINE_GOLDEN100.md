# Golden RFQ 100 — Baseline v1

Dataset: `synthetic-adversarial-v1.0`

Head evaluated: `6afe6f59942a670a80451366def6d054763da9c6`

GitHub Actions run: `Corporate RFQ CI #10`

## Purpose

This baseline tests the working safety hypothesis:

> difficult RFQ lines may be deferred, but the resolver must not auto-ACCEPT an insufficiently evidenced or wrong Product Identity.

This is **synthetic adversarial evidence**, not production accuracy evidence.

## Ground truth distribution

- ACCEPT: 15
- REVIEW_REQUIRED: 50
- REJECT: 20
- FAILURE: 15

## Current baseline

- total_cases: 100
- passed_cases: 79
- case_pass_rate: 0.79
- accepted_count: 36
- review_required_count: 31
- rejected_count: 20
- failure_count: 13
- manual_review_rate: 0.31
- exact_match_precision: 0.4166666667
- unsafe_auto_substitution_count: 21

## Result

**Working safety hypothesis is currently falsified.**

The current implementation auto-ACCEPTs 21 adversarial cases that ground truth requires to be reviewed or failed.

The dataset must not be weakened to make the metric green. The resolver/policy must be changed.

## Unsafe case classes

### Missing / untrusted manufacturer — 13

`adv-016, adv-017, adv-018, adv-020, adv-021, adv-022, adv-023, adv-024, adv-025, adv-026, adv-027, adv-028, adv-029`

Observed failure mode:

```
exact-looking MPN
+ no trusted manufacturer
→ current resolver ACCEPT
```

Required policy:

```
exact MPN
+ manufacturer not proven
→ REVIEW_REQUIRED
```

### OCR / confidence ambiguity — 1

`adv-043`

The line explicitly says OCR confidence is low but contains an otherwise exact MPN.

Required policy:

```
exact MPN
+ explicit low-confidence evidence
→ REVIEW_REQUIRED
```

### Quantity / packaging ambiguity — 2

`adv-076, adv-082`

Examples include pack multiplication and a negative quantity that the current regex can reinterpret as positive.

Required policy:

```
ambiguous pack math or invalid signed quantity
→ FAILURE / REVIEW
→ never auto-ACCEPT
```

### Analogue / replacement intent — 5

`adv-088, adv-089, adv-095, adv-096, adv-097`

Observed failure mode:

```
exact MPN appears inside a request for analogue / replacement / equivalent
→ current resolver treats the MPN as requested exact product
→ ACCEPT
```

Required policy:

```
analogue / replacement intent
→ separate AnalogueDecision
→ Product Identity must not auto-ACCEPT the referenced MPN as the requested product
```

## Positive evidence

All 20 explicitly conflicting critical-attribute cases were classified as REJECT as expected.

This confirms that the previously added `poles/current` conflict gate is working on the adversarial set.

## Next remediation slice

`RFQ-SAFE-001.2 — Golden 100 Unsafe 21 → Zero Unsafe Auto-Accepts`

Do not optimize overall accuracy first.

Priority order:

1. require trusted manufacturer for automatic exact acceptance;
2. detect analogue/replacement intent and route to review/separate decision;
3. detect invalid/ambiguous quantity and packaging semantics;
4. propagate low-confidence evidence into policy;
5. rerun the same immutable Golden 100.

## Exit criteria

- Golden dataset unchanged
- unsafe_auto_substitution_count = 0
- no regression in critical-attribute conflict rejection
- all code quality gates PASS
- baseline comparison recorded
