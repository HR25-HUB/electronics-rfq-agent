$ErrorActionPreference = "Stop"
uv sync --extra dev
uv run pytest -q
Write-Host "Ready. Open rfq-commercial-conversion-engine.code-workspace"
