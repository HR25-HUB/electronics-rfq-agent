# GitHub Copilot workflow

## Start a task

Use the repository prompt:
`/rfq-commercial-implement`

or ask:

> Read AGENTS.md and ARCHITECTURE.md. Implement issue X as the smallest vertical slice. Write the regression test first and preserve all commercial invariants.

## Review

Use:
`/rfq-commercial-review`

before opening a PR.

## Recommended issue size

One issue should normally change one business capability:
- qualification rule;
- resource policy;
- quote protection gate;
- follow-up policy;
- one objection branch;
- KT37/KT38 invariant;
- one external adapter.

Avoid "implement all Bitrix24" or "add AI" issues.

## Evidence expected from Copilot

Every implementation answer should include:
- invariant changed/preserved;
- tests added;
- commands run;
- residual risk;
- next smallest slice.
