# NUIF-CODING-AGENTS-BENCHMARK-001.A1 — Frozen agent task

## Purpose
Compare Google Antigravity and GitHub Copilot on the **same** source commit, task, evaluation criteria and time budget. This task describes expected software behavior; it is not evidence that the software passes.

- Repository: `HR25-HUB/electronics-rfq-agent`
- Baseline commit: `fcca4f22b18d71fd1547ddbcf2919b5edad4b29d`
- Scope: `src/electronics_rfq_agent/parser.py`, `src/electronics_rfq_agent/models.py`, related tests; no pricing or ERP behavior changes.
- Dataset: synthetic only, never real customer data.
- Prohibited: production credentials, publishing quotes, external mutations, changing independent benchmark tests, weakening lint/type/test gates.

## Observed implementation risk
`RFQParser._parse_json_response` catches Pydantic `ValidationError`, logs a warning and `continue`s, thereby omitting a row from the returned collection. `RFQLineItem.sanitize_part_number` forbids non-ASCII characters. The baseline regression test supplied here expects the synthetic Cyrillic part number to remain intact.

## Required behavior
1. Preserve every valid RFQ item, including valid non-ASCII (e.g. Cyrillic) part-number identifiers.
2. Do not silently omit any invalid item. If an item cannot be represented safely, fail clearly with an `RFQParseError` identifying its source row, rather than returning a misleading partial RFQ.
3. Never invent part numbers, quantities, manufacturers, dates or notes.
4. Preserve original part identifiers except for explicitly documented whitespace normalization.
5. Do not silently replace invalid quantities with defaults as part of the fix.
6. Keep Pydantic v2, Python >=3.10 and existing API contracts where feasible.
7. Add production-unit tests for success, failure and multiple-item cases without modifying benchmark oracle assertions.
8. Ensure existing project CI remains passing and attach real command logs.

## Benchmark execution
1. Start each agent from the exact baseline SHA in separate worktrees and separate branch names (not from this benchmark setup branch).
2. Give both agents this exact task text and equal permissions, time limits and environment information.
3. Hold independent evaluator data out of both agents' worktrees.
4. Run the known baseline control and failing test **before** agent execution; record timestamp, command, exit code and stdout/stderr.
5. After each agent run, apply its patch to a clean baseline checkout and run the same evaluation commands.
6. Keep external model/API usage disabled for deterministic parsing tests.

## Local reproduction (expected RED on baseline)
```bash
uv sync --extra dev
uv run pytest -q -o addopts= benchmark/tests/test_rfq_preservation.py
```

## Required report
Record baseline SHA, agent/model/version, permissions, execution time, intervention count, reported consumption, diff SHA, tests, reviewer assessment, independent holdout results and any failures. Mark any unavailable measurement as `NOT_VERIFIED`.

## Stop conditions
Stop for production secrets, network writes, incompatible data contracts, changes to evaluator tests, or unexplained failures. Human approval required for PR merge.

## Evidence status at authoring
Repository source was reviewed through GitHub connector. The test expectation is inferred from source. **No test execution has been performed yet.**
