#requires -Version 5.1
<#
.SYNOPSIS
  Install local demo dependencies for VOXMETRIKS (UTF-8 safe, no secrets printed).
#>
[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$RepoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $RepoRoot

function Test-CommandExists {
    param([string]$Name)
    return [bool](Get-Command $Name -ErrorAction SilentlyContinue)
}

function Get-PythonMajorMinor {
    param([string]$PythonExe)
    $out = & $PythonExe -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')" 2>$null
    if (-not $out) { return $null }
    return [version]$out.Trim()
}

Write-Host "=== VOXMETRIKS setup_demo ==="
Write-Host "RepoRoot: $RepoRoot"

# --- Python >= 3.11 ---
$pythonCandidates = @('python', 'py')
$pythonExe = $null
$minPy = [version]'3.11'
foreach ($cand in $pythonCandidates) {
    if (-not (Test-CommandExists $cand)) { continue }
    try {
        if ($cand -eq 'py') {
            $ver = & py -3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')" 2>$null
            if ($ver -and ([version]$ver.Trim() -ge $minPy)) {
                $pythonExe = 'py'
                $scriptArgs = @('-3')
                break
            }
        } else {
            $ver = Get-PythonMajorMinor -PythonExe $cand
            if ($ver -and $ver -ge $minPy) {
                $pythonExe = $cand
                $scriptArgs = @()
                break
            }
        }
    } catch { }
}

if (-not $pythonExe) {
    Write-Error "Python >= 3.11 is required but was not found on PATH."
    exit 1
}
Write-Host "OK Python (>=3.11) via: $pythonExe"

# --- Node / npm ---
if (-not (Test-CommandExists 'node')) {
    Write-Error "Node.js is required but was not found on PATH."
    exit 1
}
if (-not (Test-CommandExists 'npm')) {
    Write-Error "npm is required but was not found on PATH."
    exit 1
}
$nodeVer = (node --version 2>$null)
$npmVer = (npm --version 2>$null)
Write-Host "OK Node $nodeVer / npm $npmVer"

# --- Backend venv + deps ---
$BackendDir = Join-Path $RepoRoot 'apps\backend'
$VenvDir = Join-Path $BackendDir '.venv'
$VenvPython = Join-Path $VenvDir 'Scripts\python.exe'

if (-not (Test-Path $VenvDir)) {
    Write-Host "Creating venv at apps/backend/.venv ..."
    Push-Location $BackendDir
    try {
        if ($pythonExe -eq 'py') {
            & py -3 -m venv .venv
        } else {
            & $pythonExe -m venv .venv
        }
    } finally {
        Pop-Location
    }
}

if (-not (Test-Path $VenvPython)) {
    Write-Error "venv python missing: $VenvPython"
    exit 1
}

$Requirements = Join-Path $BackendDir 'requirements.txt'
$PyProject = Join-Path $BackendDir 'pyproject.toml'
$PoetryLock = Join-Path $BackendDir 'poetry.lock'

Push-Location $BackendDir
try {
    if (Test-Path $Requirements) {
        Write-Host "Installing backend deps via pip -r requirements.txt ..."
        & $VenvPython -m pip install --upgrade pip
        & $VenvPython -m pip install -r requirements.txt
    } elseif ((Test-Path $PyProject) -and (Test-CommandExists 'poetry')) {
        Write-Host "Installing backend deps via poetry ..."
        if (Test-Path $PoetryLock) {
            poetry install --no-interaction
        } else {
            poetry install --no-interaction
        }
    } elseif (Test-Path $PyProject) {
        Write-Host "Installing backend deps via pip + pyproject.toml ..."
        & $VenvPython -m pip install --upgrade pip
        & $VenvPython -m pip install -e .
    } else {
        Write-Error "No requirements.txt or pyproject.toml under apps/backend."
        exit 1
    }
} finally {
    Pop-Location
}
Write-Host "OK backend dependencies"

# --- Frontend deps ---
$FrontendDir = Join-Path $RepoRoot 'apps\frontend'
$LockFile = Join-Path $FrontendDir 'package-lock.json'
Push-Location $FrontendDir
try {
    if (Test-Path $LockFile) {
        Write-Host "Installing frontend deps via npm ci ..."
        npm ci
    } else {
        Write-Host "Installing frontend deps via npm install ..."
        npm install
    }
} finally {
    Pop-Location
}
Write-Host "OK frontend dependencies"

# --- Warehouse presence ---
$DuckDb = Join-Path $RepoRoot 'data\warehouse\voxmetrik.duckdb'
if (-not (Test-Path $DuckDb)) {
    Write-Warning "Missing warehouse: data/warehouse/voxmetrik.duckdb — restore from DEMO-RUNTIME or seed after password is configured."
} else {
    Write-Host "OK warehouse present: data/warehouse/voxmetrik.duckdb"
}

# --- Seed gate (no secrets printed) ---
$BackendEnv = Join-Path $BackendDir '.env'
$hasPasswordEnv = [bool]$env:DEMO_ACCOUNT_PASSWORD
$hasBackendEnv = Test-Path $BackendEnv

if (-not $hasPasswordEnv -and -not $hasBackendEnv) {
    Write-Warning "DEMO_ACCOUNT_PASSWORD not in process env and apps/backend/.env missing — seed will not run from this script."
} elseif (-not $hasPasswordEnv -and $hasBackendEnv) {
    Write-Host "apps/backend/.env present (contents not printed). Seed only if DEMO_ACCOUNT_PASSWORD is set in that file or process env."
} else {
    Write-Host "DEMO_ACCOUNT_PASSWORD is set in process environment (value not printed)."
}

Write-Host "=== setup_demo complete ==="
Write-Host "Next: .\scripts\start_demo.ps1  (after .env + duckdb are ready)"
exit 0
