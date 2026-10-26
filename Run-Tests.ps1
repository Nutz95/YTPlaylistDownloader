#Requires -Version 5.1
<#
.SYNOPSIS
  Ensure .venv (Python 3.14) and dev dependencies, then run the full pytest suite.
#>
param(
    [string]$RepoRoot = $PSScriptRoot,
    [string[]]$PytestArgs = @()
)

$ErrorActionPreference = "Stop"

function Write-Step([string]$Message) {
    Write-Host "==> $Message" -ForegroundColor Cyan
}

Write-Step "Repo: $RepoRoot"
Set-Location -LiteralPath $RepoRoot

$ensureVenv = Join-Path $RepoRoot "tools\Ensure-Python314Venv.ps1"
$venvPython = & $ensureVenv -RepoRoot $RepoRoot

Write-Step "Installing package and dev dependencies"
& $venvPython -m pip install -e ".[dev]"
if ($LASTEXITCODE -ne 0) {
    throw "pip install -e .[dev] failed"
}

Write-Step "Running pytest"
& $venvPython -m pytest @PytestArgs
if ($LASTEXITCODE -ne 0) {
    throw "pytest failed with exit code $LASTEXITCODE"
}

Write-Host "All tests passed." -ForegroundColor Green
