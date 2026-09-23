$ErrorActionPreference = "Stop"
uv run ruff check .
uv run pytest -q
