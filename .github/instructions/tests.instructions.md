---
applyTo: "**/tests/**/*.py"
---

# Test Instructions

- Prefer deterministic unit and contract tests.
- Every safety bug receives a regression test.
- Golden RFQ 100 is immutable unless a separately reviewed dataset version is created.
- Hard safety gate: unsafe_auto_substitution_count == 0.
- Test infrastructure failures separately from business outcomes.
- Mock external HTTP/OpenSearch in CI; production probes are manual and human-approved.
