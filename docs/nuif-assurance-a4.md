# NUIF-SDD-ASSURANCE-001.A4 — Ground Truth, Independent Review, Evidence

## Status and scope

**Draft; not approval-ready.** This increment provides the typed evaluation contract, conservative false-accept metric, independent review attestation contract and synthetic contract tests. It does **not** contain real supplier RFQ records or verified independent review signatures. No production or pricing code is changed by A4.

## Ground Truth contract

Each case uses a pseudonymous case ID, SHA-256 of the source document, two independent expert labels, optional adjudication, and a prediction from the exact frozen system candidate. Valid labels: `matched`, `alternative`, `ambiguous`, `missing`, `erp_error`. Never treat `not_found` on the existing QuoteAgent as proof of a physically absent supplier item, because A3 uses it as a compatibility state for unapproved alternatives.

The baseline evaluator uses `matched` as the only automatic acceptance label; all other predictions are non-accepting. It blocks if the manifest is synthetic, not sanitized, contains fewer than 30 cases, has unresolved expert disagreements, has any false-positive automatic match, or has no predicted matches. **The 30-case threshold and zero-false-accept tolerance are initial gate parameters, not a statistically validated production policy.** Passing this validator does NOT independently prove real provenance, privacy clearance, or acceptable production risk.

## Human expert data creation

1. A data owner selects historically completed RFQ and supplier reply pairs in a read-only internal environment. Before use, obtain organizational authorization and document permitted processing purposes and retention.
2. Keep original source documents and customer/supplier data in approved restricted storage. Never commit them or upload to public external LLM tools.
3. Two experts independently label matching outcomes. Resolve disagreements with a third adjudicator and preserve a disagreement audit trail.
4. Generate a minimized JSON manifest with hashes, case IDs, labels and provenance pointers only. The source material remains inaccessible to external tools.
5. Replay a frozen system version on exactly the labelled cases. Record commit SHA and deterministic result hashes. Distinguish the component under test: customer RFQ → ERP vs supplier reply → RFQ. No supplier-matching quality claim is allowed until that component actually exists.
6. Review errors by class, manufacturer, MPN, and provenance confidence. Approve minimum sample size and acceptable false-accept confidence interval with business owners.

## Independent Goldfish re-review

**Mandatory five separate reviewers with independent context**:

| Perspective | Focus |
|---|---|
| problem_validity | Is DR-001 the right problem? |
| comprehension | Are not_found vs needs_review semantics comprehensible? |
| technical_critique | Can an alternative still leak into quotes, audit, or pricing? |
| complexity_control | Is migration scoped safely without a duplicate SDLC? |
| implementation_readiness | Are tests, rollback, compatibility, monitoring sufficient? |

Each reviewer receives the **same immutable diff and design artifact hash** and submits an authenticated GitHub review or an approved internal signed attestation. Author-side notes or separate fictional personas in one conversation are **not** independent reviews.

## Approval and SHA-binding

Store a release candidate's source commit SHA in an external evidence bundle after the commit exists. Do not create a new commit that embeds its own commit SHA: this would change the hash and invalidate the attestation. The A4 `approval_evidence.py` currently validates structure and intentionally **always rejects release approval** until GitHub review identity/status, check-run conclusions, data provenance, and authorized human approval are verified by a trusted integration.

Critical distinction: source SHA alone does not identify the tested GitHub PR merge commit. For final approval bind CI to the tested merge candidate, GitHub PR head and base SHA, and verify no base branch updates invalidated the result.

## Open items

- **DR-001**: implementation and regression tests completed; independent closure not attested.
- **DR-002**: ERP exceptions represented as not_found.
- **DR-003**: existing agent does not perform supplier reply matching.
- **DR-004**: SupplierQuoteLine provenance contract missing.
- **DR-006**: needs_review status and consumer compatibility need an ADR and explicit approval.
- Real expert dataset: **unavailable / unverified**.
- Independent reviews: **not attested**.
- Human sign-off: **not supplied**.

## Definition of Done

A4 remains blocked until a real, authorized, externally verifiable and immutable dataset plus expert ground truth is available, all findings are resolved or explicitly approved under policy, five independent reviews are authenticated, and real CI/approval metadata are verified for the exact release candidate. Do not merge draft PRs solely because synthetic tests pass.
