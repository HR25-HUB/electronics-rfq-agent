---
applyTo: "projects/rfq-commercial-conversion-engine/**"
---

Read `projects/rfq-commercial-conversion-engine/AGENTS.md` before changing code.

Preserve these invariants:
- silence never becomes approval;
- dispatched quote versions are immutable;
- AI proposes/extracts, deterministic policy decides;
- KT37 needs explicit current-version customer evidence;
- KT38 validates quote version, quantity, price and currency;
- 1C cannot block KT38;
- COLD_CALCULATION is a low-cost path, not rejection.

Prefer the smallest test-backed vertical slice. Every policy change needs a regression test.
