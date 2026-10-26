#Requires -Version 5.1
<#
.SYNOPSIS
  Ensure .venv with Python 3.14, install runtime deps, run the local web UI.
#>
param(
    [string]$RepoRoot = $PSScriptRoot
)

$ErrorActionPreference = "Stop"

function Write-Step([string]$Message) {
    Write-Host "==> $Message" -ForegroundColor Cyan
}

Write-Step "Repo: $RepoRoot"
Set-Location -LiteralPath $RepoRoot

$ensureVenv = Join-Path $RepoRoot "tools\Ensure-Python314Venv.ps1"
$venvPython = & $ensureVenv -RepoRoot $RepoRoot

Write-Step "Installing runtime package"
& $venvPython -m pip install --upgrade pip
if ($LASTEXITCODE -ne 0) {
    throw "pip upgrade failed"
}
& $venvPython -m pip install -e .
if ($LASTEXITCODE -ne 0) {
    throw "pip install -e . failed"
}

Write-Step "Starting YTPlaylistDownloader"
& $venvPython -m ytpd
if ($LASTEXITCODE -ne 0) {
    throw "Application exited with code $LASTEXITCODE"
}
