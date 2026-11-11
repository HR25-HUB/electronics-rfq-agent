# NUIF-SDD-ASSURANCE-001.A2 — initial code-grounded design review

Status: **OPEN; not independently attested**. The notes below are observations by the implementation author. They MUST NOT be represented as five Goldfish sessions.

## Evidence inspected
- `src/electronics_rfq_agent/agent.py` on `main` (via GitHub connector)
- `src/electronics_rfq_agent/models.py` on `main`
- `pyproject.toml` and `.github/workflows/ci.yml` on `main`

## Findings
| ID | Perspective | Severity | Finding | Disposition |
|---|---|---|---|---|
| DR-001 | technical_critique | blocker | `_lookup_line` uses `search_parts(..., limit=1)`; the first nonexact hit can be classified `substituted` without an independent supplier matching approval. | open; no production behavior change made |
| DR-002 | technical_critique | major | Connection errors are returned as `not_found` in current code, collapsing technical failure and catalog absence. | open |
| DR-003 | problem_validity | major | Existing QuoteAgent handles customer RFQ to ERP lookup, not supplier reply to RFQ line matching. | open |
| DR-004 | comprehension | major | Dedicated SupplierQuoteLine and provenance contract are not defined. | open |
| DR-005 | complexity_control | minor | Do not stack four parallel SDD workflows; keep one canonical OpenSpec delta. | open |

## Independent review acceptance protocol
Five separately instantiated reviewer sessions must receive the SAME content-addressed design artifact manifest. They must emit one signed/identified Review per perspective. A reviewer cannot be the designer. Every blocker must be fixed and re-reviewed; a human may not waive blockers under the gate policy. Nonblocker decisions require a recorded rationale.

## Current scope
This PR adds a stand-alone assurance policy, CLI, tests, and synthetic dataset. It intentionally does not mutate QuoteAgent, ERP connectors, price calculation, RFQ catalog, supplier records, or production systems. The reference evaluator is NOT evidence of model matching accuracy.

## Required before Verified PR
1. Complete independent reviews with verifiable session provenance.
2. Implement and independently verify fixes on a separately approved change.
3. Produce non-synthetic business Eval evidence and requirement-to-test traceability.
4. Attach real CI artifacts, commit SHA, and human approval.
5. Make approval job green on the exact merge candidate commit.
