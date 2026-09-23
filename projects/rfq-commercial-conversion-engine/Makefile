.PHONY: bootstrap test lint verify api demo

bootstrap:
	uv sync --extra dev

test:
	uv run pytest -q

lint:
	uv run ruff check .

verify: lint test

api:
	uv run uvicorn rfq_cc.api:app --reload --port 8010

demo:
	uv run rfq-cc demo
