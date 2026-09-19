$ErrorActionPreference = "Stop"

Write-Host "== OSS core =="
uv run ruff format --check .
uv run ruff check .
uv run mypy src/ --strict
$env:ERFA_USE_MOCK = "true"
$env:ANTHROPIC_API_KEY = "test-key-not-real"
uv run pytest tests/ --cov=src --cov-fail-under=80

Write-Host "== Corporate Product Identity =="
Push-Location corporate
try {
    uv run ruff format --check .
    uv run ruff check .
    uv run pyrefly check
    uv run pytest
    uv run python scripts/evaluate_golden.py tests/golden/golden100-adversarial.jsonl
}
finally {
    Pop-Location
}

Write-Host "All checks passed."
