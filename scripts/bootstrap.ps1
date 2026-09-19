$ErrorActionPreference = "Stop"

if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
    throw "uv is required. Install it from https://docs.astral.sh/uv/"
}

Write-Host "Syncing OSS core..."
uv sync --extra dev

Write-Host "Syncing corporate Product Identity..."
Push-Location corporate
try {
    uv sync --extra dev
}
finally {
    Pop-Location
}

Write-Host "Bootstrap complete."
