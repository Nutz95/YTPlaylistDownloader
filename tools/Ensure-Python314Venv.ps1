#Requires -Version 5.1
<#
.SYNOPSIS
  Resolve Python 3.14 and ensure a repo-local .venv exists.
.OUTPUTS
  Absolute path to .venv\Scripts\python.exe
#>
param(
    [Parameter(Mandatory = $true)]
    [string]$RepoRoot
)

$ErrorActionPreference = "Stop"

function Resolve-Python314 {
    $pyLauncher = Get-Command py -ErrorAction SilentlyContinue
    if ($null -ne $pyLauncher) {
        $versionText = & py -3.14 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"
        if ($LASTEXITCODE -eq 0 -and $versionText.Trim() -eq "3.14") {
            return @{ Exe = "py"; Args = @("-3.14") }
        }
    }

    $pythonCmd = Get-Command python -ErrorAction SilentlyContinue
    if ($null -ne $pythonCmd) {
        $versionText = & python -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"
        if ($LASTEXITCODE -eq 0 -and $versionText.Trim() -eq "3.14") {
            return @{ Exe = $pythonCmd.Source; Args = @() }
        }
    }

    throw "Python 3.14 is required. Install it and ensure 'py -3.14' works."
}

$venvPython = Join-Path $RepoRoot ".venv\Scripts\python.exe"
if (-not (Test-Path -LiteralPath $venvPython)) {
    Write-Host "==> Creating .venv with Python 3.14" -ForegroundColor Cyan
    $python = Resolve-Python314
    & $python.Exe @($python.Args + @("-m", "venv", (Join-Path $RepoRoot ".venv")))
    if ($LASTEXITCODE -ne 0) {
        throw "Failed to create .venv"
    }
}

if (-not (Test-Path -LiteralPath $venvPython)) {
    throw "Expected venv python at $venvPython"
}

return $venvPython
