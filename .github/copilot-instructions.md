# Copilot Instructions

You are working in an RFQ automation repository with two boundaries:

1. existing reusable OSS core under `src/electronics_rfq_agent`;
2. corporate business application under `corporate/`.

Rules:

- Use DDD/Hexagonal boundaries for corporate business logic.
- Do not modify existing public OSS behavior unless the issue explicitly requires it.
- Candidate retrieval is not ProductIdentityDecision.
- Non-exact matches require review by default.
- Catalog/ERP/network failures are technical states, not NOT_FOUND.
- Never silently default ambiguous quantity to 1.
- Pricing, substitutions, customer writes and production actions require policy and human governance.
- Use Pydantic v2 contracts and deterministic tests.
- Keep diffs bounded and do not modify unrelated files.
