# Corporate RFQ Product Identity — Business Model

## 1. Business problem

Incoming B2B RFQs contain dirty, incomplete and inconsistent product descriptions. A wrong automatic match can create an incorrect quote, procurement action, margin loss or customer trust issue.

The project optimizes first for **safe acceleration of RFQ decisions**, not maximum automation.

## 2. Business flow

```text
Customer RFQ
→ line extraction / normalization
→ Product Identity candidate retrieval
→ evidence collection
→ policy gate
→ ACCEPT | REVIEW_REQUIRED | REJECT | FAILURE
→ sourcing / supplier quote
→ offer optimization
→ customer proposal
```

Current implemented scope ends at Product Identity and read-only retrieval evidence.

## 3. Value creation

1. Reduce manager time on obvious exact identities.
2. Route ambiguous/analogue cases to human review instead of hiding uncertainty.
3. Keep technical failures separate from business NOT_FOUND.
4. Create audit evidence for automated decisions.
5. Measure quality before pricing, sourcing or customer-facing writes.

## 4. Automation policy

Auto-accept requires:
- trusted manufacturer;
- normalized exact SKU;
- unambiguous quantity/UOM;
- no analogue/replacement intent;
- no low-confidence source signal;
- no critical attribute conflict.

Otherwise the line is reviewed, rejected or classified as failure.

## 5. Economic levers

Expected levers:
- lower time-to-quote;
- lower manual effort per line;
- fewer wrong substitutions;
- lower rework;
- higher proposal completeness;
- measurable review workload.

No ROI claim is made in this snapshot because real redacted company RFQs have not yet been benchmarked.

## 6. KPIs

- terminal_decision_rate
- exact_accept_precision
- top1/top3 retrieval recall
- manual_review_rate
- unsafe_auto_substitution_count
- technical_failure_classification_rate
- time_to_product_identity
- manager_correction_rate

Hard safety KPI:
`unsafe_auto_substitution_count = 0`.

## 7. Current evidence

Synthetic adversarial Golden RFQ 100:
- baseline v1: 79/100, unsafe auto-accepts 21;
- remediation v2: 100/100, unsafe auto-accepts 0.

This is engineering evidence, not production accuracy.

## 8. Next business experiment

Use 50–100 real **redacted** RFQ lines and read-only Catalog.App/OpenSearch evidence.

Decision after experiment:
- expand safe automation;
- tune retrieval;
- change review policy;
- or stop/reshape the approach if real metrics do not support it.
