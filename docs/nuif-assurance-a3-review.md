# NUIF-SDD-ASSURANCE-001.A3 — DR-001 resolution candidate

## Proposed change (not approved for production)

`QuoteAgent._lookup_line()` no longer prices or marks a non-exact ERP search result as an approved substitution. It returns `not_found` with a clearly marked manual-approval note instead. Exact part numbers (case-insensitive) still produce quotes. No supplier-specific matching was added.

## Why the existing status is `not_found`

The current quote schema supports only `found`, `not_found`, and `substituted`. Adding a first-class `needs_review` state requires changes to downstream clients, API contracts and reporting. This A3 candidate intentionally avoids that cross-service change but records it as **DR-006 (major open)**. The business team must not treat this `not_found` count as a confirmed physical absence from the catalog.

## Author-side verification plan
- Alternative candidate: no unit price, no extended price, no ERP pricing call
- Exact candidate: existing quote behavior preserved
- Missing part: no price
- Review policy and all A2 gates remain fail-closed

## Findings and decisions
| ID | Severity | Disposition | Evidence / next action |
|---|---|---|---|
| DR-001 | blocker | fix implemented; **independent verification pending** | `src/electronics_rfq_agent/agent.py`, `tests/test_dr001_policy.py` |
| DR-002 | major | OPEN | ERP transport errors currently represented as not_found |
| DR-003 | major | OPEN | RFQ→ERP quoting and supplier reply matching are separate domains |
| DR-004 | major | OPEN | SupplierQuoteLine provenance contract not implemented |
| DR-006 | major | OPEN | explicit needs_review status would affect downstream schema |

## Independent re-review requirements
A genuinely separate reviewer must inspect the before/after diff without relying on this author's reasoning and evaluate:
1. Correct problem and minimal scope.
2. Clear, testable semantics, especially not_found vs needs_review.
3. Security, ERP failures, edge cases, no unintended pricing.
4. Simplicity vs domain policy and backward compatibility.
5. Implementation readiness, tests, migration and rollout.

A review generated in the same author session does **not** satisfy independence. Findings cannot be closed solely by author declaration.

## Real Eval baseline
No authenticated, de-identified, human-labelled real supplier quote/RFQ pairs were available in the examined repository files. **Baseline NOT VERIFIED.** Do not relabel the synthetic 20-case dataset as real data. A real baseline requires:
- A read-only source of consented historical RFQ lines and supplier replies
- Independent expert labels: matched, alternative, ambiguous, missing, ERP failure
- Immutable dataset version and SHA-256
- False-accept rate by manufacturer/MPN and coverage, with expert-reviewed disagreements
- No source customer names, addresses, contract prices, supplier credentials or PII in external tools

## Evidence bundle state
- Source commit SHA: capture from GitHub PR head after CI, not from user text.
- CI run IDs: capture after tests have completed.
- Independent review sessions: **MISSING**.
- Expert baseline: **MISSING**.
- Human approval: **MISSING**.
- Verified PR: **BLOCKED**.

The A2 `assurance/review_gate.py` is deliberately strict and cannot pass without these required artifacts. No file claiming a successful approval is generated.
