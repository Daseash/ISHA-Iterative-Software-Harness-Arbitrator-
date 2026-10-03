# install.ps1 — one-command ISHA installer (Windows).
#
#   powershell -NoProfile -ExecutionPolicy Bypass -File install.ps1
#
# Creates .venv\, installs the wheel (or falls back to source), and copies
# .env.example to .env so `isha doctor` has a place to read keys from.
# Usage afterwards:  .venv\Scripts\isha doctor   →   isha fix --help

$ErrorActionPreference = 'Stop'
$Repo = $PSScriptRoot
$Venv = Join-Path $Repo '.venv'
$Wheel = Get-ChildItem (Join-Path $Repo 'dist\isha_fix-*.whl') -ErrorAction SilentlyContinue |
  Sort-Object LastWriteTime -Descending | Select-Object -First 1

Write-Host "ISHA installer (repo: $Repo)"

# 1. Python
py -3 --version 2>$null
if ($LASTEXITCODE -ne 0) { python --version }
if ($LASTEXITCODE -ne 0) { throw 'Python 3.10+ not found on PATH' }

# 2. Virtual env
if (-not (Test-Path $Venv)) {
  Write-Host 'Creating .venv ...'
  python -m venv $Venv
}
$Py = Join-Path $Venv 'Scripts\python.exe'

# 3. Install: wheel if present, else the source tree
Write-Host 'Installing ISHA + dependencies (first run downloads a few hundred MB; torch/CUDA via docling are the bulk) ...'
& $Py -m pip install --upgrade pip | Out-Null
if ($Wheel) {
  & $Py -m pip install $Wheel.FullName
} else {
  & $Py -m pip install $Repo
}
if ($LASTEXITCODE -ne 0) { throw 'pip install failed' }

# 4. .env template
$envDst = Join-Path $Repo '.env'
if (-not (Test-Path $envDst)) {
  Copy-Item (Join-Path $Repo '.env.example') $envDst
  Write-Host "Created .env from .env.example — add your GROQ_API_KEY / GOOGLE_API_KEY"
}

# 5. Verify
& (Join-Path $Venv 'Scripts\isha.exe') --help | Out-Null
if ($LASTEXITCODE -ne 0) { throw 'isha CLI not reachable after install' }

Write-Host ''
Write-Host 'Done. Next steps:'
Write-Host "  $envDst   -> add your API keys"
Write-Host "  .venv\Scripts\isha doctor"
Write-Host "  .venv\Scripts\isha fix --repo <path-or-url> --issue '...' --apply"
