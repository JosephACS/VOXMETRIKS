#requires -Version 5.1
<#
.SYNOPSIS
  Verify demo stack: health, frontend root, warehouse verify script.
#>
[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$RepoRoot = Split-Path -Parent $PSScriptRoot
$BackendDir = Join-Path $RepoRoot 'apps\backend'
$VenvPython = Join-Path $BackendDir '.venv\Scripts\python.exe'
$failed = $false

function Test-Http {
    param([string]$Url, [string]$Label)
    try {
        $resp = Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec 10 -ErrorAction Stop
        Write-Host ("OK {0} HTTP {1} - {2}" -f $Label, $resp.StatusCode, $Url)
        return $true
    } catch {
        Write-Host ("FAIL {0} - {1} - {2}" -f $Label, $Url, $_.Exception.Message)
        return $false
    }
}

if (-not (Test-Http 'http://127.0.0.1:8000/health' 'backend /health')) { $failed = $true }
if (-not (Test-Http 'http://127.0.0.1:4200/' 'frontend /')) { $failed = $true }

$pythonExe = $null
if (Test-Path $VenvPython) {
    $pythonExe = $VenvPython
} else {
    $fallback = Get-Command python -ErrorAction SilentlyContinue
    if ($fallback) { $pythonExe = $fallback.Source }
}

if (-not $pythonExe) {
    Write-Host 'FAIL no Python for verify_final_demo_state.py'
    $failed = $true
} else {
    Write-Host ("Running verify_final_demo_state.py with: {0}" -f $pythonExe)
    Push-Location $BackendDir
    try {
        & $pythonExe 'scripts\verify_final_demo_state.py'
        if ($LASTEXITCODE -ne 0) {
            Write-Host ("FAIL verify_final_demo_state.py exit={0}" -f $LASTEXITCODE)
            $failed = $true
        } else {
            Write-Host 'OK verify_final_demo_state.py'
        }
    } finally {
        Pop-Location
    }
}

if ($failed) {
    Write-Host 'verify_demo: FAILED'
    exit 1
}
Write-Host 'verify_demo: PASSED'
exit 0
