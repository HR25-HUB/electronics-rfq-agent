# Repository Agent Contract

## Mission

Keep the OSS RFQ core reusable while developing corporate RFQ business decisions as a separate bounded application.

## Rules

- Candidate retrieval is not a business decision.
- Exact product identity and technical analogue are separate decisions.
- Pricing/customer actions are high-risk and require explicit policy/human approval.
- Technical dependency failures must never become product NOT_FOUND.
- Ambiguous quantity/UOM must never be silently defaulted.
- Reuse existing code before adding abstractions.
- Do not change public OSS API in `RFQ-SAFE-001`.

## Change budget

Prefer <= 8 changed files and one domain per PR.

## Validation

Root OSS core keeps its existing CI. Corporate changes additionally run `.github/workflows/corporate-rfq-ci.yml`.
