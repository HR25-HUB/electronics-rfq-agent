# REA-RFQ-PDF-001.A1.2.4 — Verified Extraction Foundation

Issue: #22. Status: **draft / unverified** until CI and independent review pass.

## What this branch implements

- Strict Pydantic v2 evidence, source-line and extracted-field contracts.
- Fail-closed coverage and exact-character-span verification.
- Three output statuses: BLOCKED, REVIEW_REQUIRED, VERIFIED.
- Canonical JSON and SHA-256 audit bundle with exclusive no-overwrite run folders.
- Synthetic adversarial regression tests.

## Important limits

1. **No real PDF is processed.** This branch consumes in-memory synthetic evidence.
2. The source-line registry is supplied independently; it is not an independent proof of PDF line recall.
3. Exact text-span equality proves literal provenance, **not** semantic correctness or row/column association.
4. The human approval parameter is only a hash match. A production review service MUST authenticate the reviewer and cryptographically or transactionally bind approval to the exact result and policy; do not expose this argument as an unauthenticated API.
5. Audit folders are no-overwrite at the application level, but are **not** WORM storage or secure from filesystem administrators.
6. **PydanticAI and Pydantic AI Harness runtime integration are not implemented in this foundation commit.** They require pinned dependency resolution, API smoke tests, `FunctionModel` integration tests, and revised `uv.lock`.
7. The legacy `RFQParser`, `QuoteAgent`, quote pricing and ERP behavior are intentionally unchanged.

## Local tests

```powershell
uv sync --extra dev --locked
uv run ruff check src/electronics_rfq_agent/verified_extraction tests/unit/test_verified_extraction.py
uv run ruff format --check src/electronics_rfq_agent/verified_extraction tests/unit/test_verified_extraction.py
uv run mypy src/ --strict
uv run pytest tests/unit/test_verified_extraction.py -q
```

## Next verified checkpoints

- Format/lint/mypy/pytest on Python 3.10, 3.11, 3.12 in existing CI.
- Add isolated, opt-in PydanticAI + Harness dependencies, pin `uv.lock`, run real import/API smoke checks.
- `FunctionModel` with `ALLOW_MODEL_REQUESTS=False`; prove no tool/network calls.
- Produce audit output from a real controlled test invocation, record CI run URL, collect independent human review.
- Only then promote this Draft PR from NOT VERIFIED to verified candidate.

## No production data

Never commit real customer PDFs, RFQ text, private catalog data, credentials or proprietary evidence into this public repository.
