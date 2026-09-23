# RFQ Commercial Conversion Engine

Working vertical-slice project for VS Code + Git + GitHub Copilot.

## Flow

`Qualification → Resource Allocation → Quote Protection → KT36 → Follow-Up/Objections → KT37 → KT38 → Closed-Lost`

## System boundaries

- **Bitrix24** — communications, deals, tasks, timeline, manager UX.
- **Saleor** — operational commerce and order.
- **Q2O** — qualification, policy, evidence, gates, audit.
- **1C KA 2.5** — downstream registration after KT38.

## Quick start

```powershell
cd projects/rfq-commercial-conversion-engine
uv sync --extra dev
uv run pytest -q
uv run uvicorn rfq_cc.api:app --reload --port 8010
```

Swagger: `http://127.0.0.1:8010/docs`.

## Invariants

1. Silence != approval.
2. Dispatched quote is immutable; changed terms create a new version.
3. AI extracts/proposes; deterministic policy decides.
4. KT37 requires explicit customer evidence for the current quote version.
5. KT38 checks quote version, quantity, unit price and currency.
6. 1C cannot block KT38.
7. COLD_CALCULATION is a low-cost path, not rejection.

## Copilot bootstrap prompt

> Read AGENTS.md and repository Copilot instructions. Run tests, explain the current vertical slices, then propose one smallest safe improvement without changing business invariants.
