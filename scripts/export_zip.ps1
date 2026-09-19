$ErrorActionPreference = "Stop"

$root = Resolve-Path (Join-Path $PSScriptRoot "..")
$name = "electronics-rfq-agent-corporate-full"
$out = Join-Path $root "$name.zip"

if (Test-Path $out) { Remove-Item $out -Force }

$exclude = @(".git", ".venv", "__pycache__", ".pytest_cache", ".ruff_cache")
$temp = Join-Path $env:TEMP "$name-$([guid]::NewGuid())"
New-Item -ItemType Directory -Path $temp | Out-Null

try {
    robocopy $root (Join-Path $temp $name) /E /XD $exclude /XF "$name.zip" | Out-Null
    Compress-Archive -Path (Join-Path $temp $name) -DestinationPath $out
    Write-Host "Created $out"
}
finally {
    Remove-Item $temp -Recurse -Force -ErrorAction SilentlyContinue
}
