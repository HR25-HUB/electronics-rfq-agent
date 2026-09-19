#!/usr/bin/env bash
set -euo pipefail

echo "== OSS core =="
uv run ruff format --check .
uv run ruff check .
uv run mypy src/ --strict
ERFA_USE_MOCK=true ANTHROPIC_API_KEY=test-key-not-real \
  uv run pytest tests/ --cov=src --cov-fail-under=80

echo "== Corporate Product Identity =="
(
  cd corporate
  uv run ruff format --check .
  uv run ruff check .
  uv run pyrefly check
  uv run pytest
  uv run python scripts/evaluate_golden.py tests/golden/golden100-adversarial.jsonl
)

echo "All checks passed."
