.PHONY: bootstrap check corporate-check golden

bootstrap:
	bash scripts/bootstrap.sh

check:
	bash scripts/check.sh

corporate-check:
	cd corporate && uv run ruff format --check . && uv run ruff check . && uv run pyrefly check && uv run pytest

golden:
	cd corporate && uv run python scripts/evaluate_golden.py tests/golden/golden100-adversarial.jsonl
