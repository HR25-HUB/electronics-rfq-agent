$ErrorActionPreference = "Stop"
uv run uvicorn rfq_cc.api:app --reload --host 127.0.0.1 --port 8010
