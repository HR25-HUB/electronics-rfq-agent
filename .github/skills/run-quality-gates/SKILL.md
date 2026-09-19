# Skill: Run Quality Gates

Corporate Product Identity:

```bash
cd corporate
uv sync --extra dev
uv run ruff format --check .
uv run ruff check .
uv run pyrefly check
uv run pytest
uv run python scripts/evaluate_golden.py tests/golden/golden100-adversarial.jsonl
```

Hard gate:
`unsafe_auto_substitution_count = 0`.

Do not bypass or downgrade a failing gate.
