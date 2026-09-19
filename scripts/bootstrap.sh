#!/usr/bin/env bash
set -euo pipefail

command -v uv >/dev/null 2>&1 || {
  echo "uv is required: https://docs.astral.sh/uv/" >&2
  exit 2
}

echo "Syncing OSS core..."
uv sync --extra dev

echo "Syncing corporate Product Identity..."
(
  cd corporate
  uv sync --extra dev
)

echo "Bootstrap complete."
