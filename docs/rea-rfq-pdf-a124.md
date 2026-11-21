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

## A1.2.4E — Trusted Approval Boundary

`approval.py` defines the input claim and a **TrustedApprovalVerifier Protocol**, not a
production identity service. An `ApprovalClaim` alone is untrusted input.

The approval decision is bound to `document_id`, the canonical evidence and
result SHA-256 hashes, `run_id`, `policy_version`, reviewer, issuer,
issue/expiry timestamps, and an opaque `proof`.

**Invariants:**
- No verifier or claim → REVIEW_REQUIRED (never VERIFIED).
- Evidence or extraction failure → BLOCKED irrespective of any approval.
- Changed evidence, output, run, policy, or expired approval → REVIEW_REQUIRED.
- Verifier must authenticate issuer and reviewer, check reviewer role/entitlement,
  validate proof, and atomically consume approval ID against a durable replay ledger.
- The in-repository synthetic test verifier is **not a production authentication
  mechanism** and may never be installed as the live adapter.
- The verification report stored by the extraction engine always remains
  `REVIEW_REQUIRED` without a separate, trusted approval authority; the
  `assess_approval` function returns an independent final disposition.

**Production blockers:** select an authorized approval provider, implement a
server-side trust adapter, enforce per-tenant authorization and binding to
document owner, record signed or otherwise verifiable approval evidence in
protected storage, and add security/integration tests before enabling VERIFIED
in an application workflow. No credentials or proof keys in GitHub.

**Harness status:** An isolated Python 3.12 workflow resolves
`pydantic-ai-harness==0.70.0` through uv and exercises FunctionModel +
OutputGuardrail offline. This is **a pinned direct overlay, not a complete
reproducible transitive lockfile**. Generating and committing an isolated
lockfile, with a fully locked CI run, is still required.

**Security status:** Main Trivy scanning remains blocking; do not merge this
feature branch until the existing security PR resolves findings and the full
CI matrix is green.
