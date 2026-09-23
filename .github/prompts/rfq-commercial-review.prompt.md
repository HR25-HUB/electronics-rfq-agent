---
mode: ask
description: Review RFQ Commercial Conversion changes for business-rule regressions.
---

Review the selected diff for:
- false approval paths;
- quote-version mutation;
- KT37 evidence gaps;
- KT38 quantity/price/currency/version mismatch;
- missing idempotency;
- domain depending on vendor/API code;
- 1C accidentally blocking operational order flow.

Return findings by severity and name the exact regression test to add.
