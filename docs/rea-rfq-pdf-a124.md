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

## A1.2.4F — Opt-in signed approval adapter

`verified_extraction/approval_adapter.py` provides
`SqliteHmacApprovalVerifier` as a **local single-host proof-of-concept**.
It uses HMAC-SHA256 over canonical claim fields, a trusted issuer-key map,
an independently configured allow-list of reviewer identities, and a
SQLite primary-key constraint to reject consumed approval IDs atomically.

The signing key **must not** be bundled with the extraction process, stored in
Git, logged, or provided to the LLM. The `sign_approval` helper is issuer-side
only. The verifier is constructed with keys provisioned from an approved
secret manager. No default keys, synthetic identities, or permissive fallbacks
exist in application code. The included test key and test reviewer are
synthetic fixtures only.

Security acceptance tests include signature invalidation on modified
document, run, policy, evidence hash, result hash, issuer, or reviewer;
unknown reviewer; incorrect authority key; short key rejection; atomic
one-time replay checks across separately initialized SQLite verifiers;
and no approval consumed when the run context is invalid.

**Unresolved production requirements:**
- Authenticated review UI with verified human identity and role mapping from
  enterprise SSO/Bitrix24 or another authoritative identity provider;
- tenant and business-owner scoping, key rotation, revocation and
  organizational separation of signing and verification roles;
- reliable clock source and review decision audit;
- hardened, backed-up permission-restricted approval ledger with failure
  and concurrency tests; SQLite is not a cross-region distributed ledger;
- separate trusted audit-anchor or signed receipt for approval events;
- tests of actual identity and secret-management integrations.

`assess_approval` returns a final disposition, while the stored extraction
`VerificationReport` remains `REVIEW_REQUIRED` in the absence of trusted
end-to-end authorization. The current module is not invoked by
`RFQParser`, `QuoteAgent` or ERP pathways.

## Locked Harness — outstanding

Current opt-in CI executes `pydantic-ai-harness==0.70.0` on Python 3.12
without a committed isolated transitive lockfile. This is **not** sufficient
for A1.2.4F locked-dependency acceptance.

Recommended independent build contract:
1. Create separate Python 3.12 environment/project for Harness, do not raise
   the existing `electronics-rfq-agent` Python >=3.10 minimum.
2. Resolve `pydantic-ai-harness==0.70.0` and dev/test dependencies with uv.
3. Commit the generated isolated `uv.lock`, record the uv version and
   package hashes; run `uv sync --locked` in offline CI integration job.
4. Run Ruff, mypy, pytest and vulnerability scans on the locked runtime.
5. Do not claim this gate passed until the actual lockfile is committed and
   the locked GitHub workflow succeeds.

## A1.2.4F — Verified implementation status (2026-11-21)

- `approval_adapter.py` implements an **opt-in** local HMAC-SHA256 verifier
  with configured trusted issuer keys and reviewer entitlement mapping.
  A SQLite unique approval ledger makes the same `approval_id` usable once.
  Test-only keys and reviewers are synthetic; no production secret is stored.
- `test_signed_approval_adapter.py` covers invalid signature, changed
  issuer/reviewer/run/document/policy/evidence/result, wrong key, revoked
  entitlement, persistent replay and end-to-end verification.
- Isolated Python 3.12 Harness environment is specified at
  `harness-env/pyproject.toml`, with a pinned direct package
  `pydantic-ai-harness==0.70.0`.
- GitHub Actions generates `harness-env/uv.lock`, checks its SHA-256 against
  `harness-env/LOCKFILE-SHA256`, then runs `uv sync --locked` and tests
  with no external LLM requests. Its resolved lockfile is uploaded as
  `harness-312-uv-lock` artifact for independent review.
- Reviewed lockfile SHA-256:
  `7c85884af7e4c8cb2fd852533121753c008db1d53a73c080ccb3f592746f9799`
  (63 packages, Python 3.12, observed in CI run 44907704010).
- **Remaining release requirement:** commit that exact resolved lockfile to
  `harness-env/uv.lock` and change CI from regeneration to
  `uv sync --locked` against the committed file. A checksum only is not
  equivalent to a committed full dependency lock.
- Authentication, tenant-scoped authorization, KMS-managed issuer keys,
  signed audit anchors, and cross-host replay prevention remain outside
  this local proof-of-concept.
- Main CI Trivy failures remain a blocking dependency-security issue tracked
  by SEC-001 / PR #11. No severity relaxation or new ignore was added.
