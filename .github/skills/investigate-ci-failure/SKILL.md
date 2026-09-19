# Skill: Investigate CI Failure

1. Identify the first failing deterministic step.
2. Separate tooling/style failure from functional/safety failure.
3. Extract exact diagnostics.
4. Do not change business expected outcomes to make CI green.
5. Make the smallest fix.
6. Re-run the same gate.
7. Re-run Golden RFQ 100 if Product Identity behavior could change.
8. Record before/after evidence in PR.
