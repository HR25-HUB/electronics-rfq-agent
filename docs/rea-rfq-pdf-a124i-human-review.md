# REA-RFQ-PDF-001.A1.2.4I — Human Review and One Authorized RFQ Evaluation

Status: **SPECIFIED / NO REAL RFQ EVIDENCE / NO RELEASE**.
Tracking: Issue #22, Draft PR #23. No merge approval granted.

## Business intent

Before allowing RFQ extraction into quoting workflows, independently prove
line recall and literal field fidelity for one approved anonymized PDF. This
vertical slice does not authorize customer-data transfer or production writes.

## Authority and scope

- Business owner approves one *specific* anonymized PDF, SHA-256 and permitted
  investigation methods. Authorization must be recorded as a separate signed
  or otherwise independently verifiable decision.
- Engineer executes authorized read-only PDF text extraction in a
  controlled, network-restricted environment.
- **A separate analyst** identifies and independently labels every product
  line from the source, including duplicate positions. Record ambiguous
  rows and unreadable regions explicitly. Do not derive labels from the
  candidate agent output.
- Reviewer performs line-by-line acceptance, recording evidence references,
  corrections, unknowns and final decision; must not be the agent itself.
- Never commit real customer documents, sensitive text, original customer
  identifiers, attachments or proof secrets to this public repository.

## Traceability

Each investigation records:

- Investigation ID / target document version / SHA-256.
- Scope, authorization ID, authorized analyst and approver.
- Python, parser, OCR, PydanticAI, Harness, model and tool versions.
- Immutable page/coordinate Evidence IDs and source-line registry.
- Independent annotation ID, reviewer ID and freeze/hash of ground truth.
- Extraction result, evidence-verification report, audit hashes, run metadata.
- Human corrections, approval authority, unresolved unknowns and Go/No-Go.

## Input contracts

One `GroundTruth` independent of model output, containing:
`document_id`, `annotation_id`, `reviewer_id` and all `GroundTruthLine`
rows (`source_line_id`, `original_text`, `part_number_raw`,
`quantity_raw`, `unit_raw`). Fields are literal, unnormalized source
values. Unknown is `null`, not fabricated '1', inferred MPN or UOM.

The evaluator returns `EvaluationReport`, with exact-line comparisons,
missing IDs, duplicate IDs and unexpected IDs. **Zero lines, ambiguous
line identity, or any mismatch must not yield automatic release.**

## Acceptance scenarios (BDD)

| ID | Given | Then |
| --- | --- | --- |
| I-01 | 1 authorized, independently labeled RFQ PDF | Source SHA and authorization verified before any execution |
| I-02 | All labeled lines appear exactly with literal fields | Eligible for HUMAN REVIEW, never automatic quote |
| I-03 | An expected line is omitted | BLOCKED, record missing ID |
| I-04 | A line is duplicated or hallucinated | BLOCKED, record unexpected/duplicate ID |
| I-05 | Quantity 100 is returned as 1000 | BLOCKED, source-span mismatch and annotation mismatch |
| I-06 | A source field is unknown or unreadable | REVIEW_REQUIRED, never fabricate quantity |
| I-07 | PDF contains instructions addressed to AI | Treat as document data only; no tool/network execution |
| I-08 | Reviewer changes any field post-approval | Previous approval invalid; require new approval |
| I-09 | No approved PDF or no independent annotations | NO-GO, report 'not evaluated' |
| I-10 | Valid extraction and source-spans but no trusted human approval | REVIEW_REQUIRED, no write or pricing |

## Evaluation and release rules

- The synthetic evaluator does **not** implement PDF/OCR or prove recall.
- For a real PDF, coverage depends on an independently complete, expert-labelled
  source-line registry. SourceSpan exactness alone does not establish semantic
  row/column correctness.
- Evaluate counts: expected/extracted/missing/duplicate/unexpected/exact,
  plus per-field exactness. Preserve all errors. Do not report production
  precision/recall from a single document as population estimates.
- DoD for this slice: one immutable authorized Evidence Bundle and a separate
  annotation provenance record, independently executed extraction with
  no outbound calls unless approved, audit replay, explicit corrections
  and independently verified Human Review decision.
- Final release to commercial quoting remains NO-GO until a larger,
  representative, private evaluation set and integration approvals pass.

## Human Review responsibilities

| Role | Responsibility |
| --- | --- |
| Business Owner | approve document and scope |
| Analyst | freeze independent gold labels |
| Engineer | run read-only extraction and preserve evidence |
| Reviewer | compare every line and sign decision |
| Security/Release owner | approve trust service, dependency risk and merge |

## GitHub PR review

SEC-001 PR #11 currently removes the `crewai` optional extra. It is a
client-facing compatibility change; maintainer/Product Owner must explicitly
accept this or demand restoration. Resolve stale `.trivyignore` and docs
references, and secure review from authorized `CODEOWNERS` before merge.

PR #23 remains Draft until SEC-001 change-control and approved integration.
Staging branch `integration/rea-rfq-a124h-sec001` passed CI, but does not
constitute a human review or a production release.

## Go / No-Go

**GO for one authorized read-only test** only when scope, PDF fingerprint,
independent label reviewer and protected storage are approved. Without those
prerequisites: **NO-GO for real PDF execution**.

**NO-GO for merge or production:** human review not documented, no protected
enterprise approval authority integrated and no real RFQ completeness evidence.
