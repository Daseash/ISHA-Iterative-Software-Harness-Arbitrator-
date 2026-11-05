# docker_maintain.ps1 — one-command Docker image maintenance for ISHA.
#
# Usage (from anywhere):
#   powershell -NoProfile -File scripts\docker_maintain.ps1            # prune + build both + manifest
#   powershell -NoProfile -File scripts\docker_maintain.ps1 -SkipBuild # prune + manifest only
#
# Tags: <image>:<version> (from pyproject.toml) + <image>:latest, with
# org.isha.image / org.isha.version labels. Dangling images are pruned on
# every run so no untagged cruft survives.

param(
  [switch]$SkipBuild
)

$ErrorActionPreference = 'Stop'
$Repo = Split-Path -Parent $PSScriptRoot

function Get-IshaVersion {
  $line = Select-String -Path (Join-Path $Repo 'pyproject.toml') -Pattern '^version\s*=\s*"(.*?)"' |
    Select-Object -First 1
  if (-not $line) { throw 'pyproject.toml: no version line found' }
  return $line.Matches[0].Groups[1].Value
}

$ver = Get-IshaVersion
Write-Host "ISHA docker maintain — version $ver (repo: $Repo)"

Write-Host "`n[1/4] pruning dangling images..."
& docker image prune -f | Out-Null

if (-not $SkipBuild) {
  Write-Host "[2/4] building isha:$ver + isha:latest ..."
  & docker build -t "isha:$ver" -t 'isha:latest' `
      --label "org.isha.image=agent" --label "org.isha.version=$ver" `
      -f (Join-Path $Repo 'Dockerfile') $Repo
  if ($LASTEXITCODE -ne 0) { throw 'isha agent build failed' }

  Write-Host "[3/4] building isha-sandbox:$ver + isha-sandbox:latest ..."
  & docker build -t "isha-sandbox:$ver" -t 'isha-sandbox:latest' `
      --label "org.isha.image=sandbox" --label "org.isha.version=$ver" `
      -f (Join-Path $Repo 'sandbox.Dockerfile') $Repo
  if ($LASTEXITCODE -ne 0) { throw 'isha-sandbox build failed' }
} else {
  Write-Host '[2/4] skipped build'
  Write-Host '[3/4] skipped build'
}

Write-Host "`n[4/4] manifest:"
& docker images 'isha*' --format '  {{.Repository}}:{{.Tag}}  {{.Size}}'
& docker images 'swebench*' --format '  (transient eval) {{.Repository}}:{{.Tag}}  {{.Size}}' |
  ForEach-Object { if ($_.Trim()) { $_ } }
Write-Host "`ndone."
