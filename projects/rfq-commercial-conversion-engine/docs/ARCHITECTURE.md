# Architecture

## Context

```text
Customer
  ↕
Bitrix24 (interaction / manager UX)
  ↕
Q2O Commercial Conversion Engine
  ↕
Saleor (quote / operational order)
  ↓
1C KA 2.5 (async registration)
```

## Internal control layers

1. **Pre-Quote Qualification** — need, decision mechanics, win criterion.
2. **Resource Allocation** — HOT/WARM/COLD/REVIEW controls processing budget.
3. **Quote Protection** — self-contained quote + presentation evidence + valid-until.
4. **Quote Response Lifecycle** — receipt, objections, follow-up, renegotiation.
5. **KT37 Gate** — explicit decision evidence for current quote version.
6. **KT38 Gate** — exact commercial match before order is accepted.
7. **Closed-Lost Intelligence** — structured reason and price delta.

## Dependency rule

`domain ← application ← adapters/API`

Domain code must not import FastAPI or vendor SDKs.

## Authority model

`AI extraction → evidence → deterministic policy → HITL when required → execution → audit`.
