#requires -Version 5.1
<#
.SYNOPSIS
  Start local demo backend + frontend. Prints only public URLs (no secrets).
#>
[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$RepoRoot = Split-Path -Parent $PSScriptRoot
$PidDir = Join-Path $RepoRoot 'scripts\.demo-pids'
$BackendDir = Join-Path $RepoRoot 'apps\backend'
$FrontendDir = Join-Path $RepoRoot 'apps\frontend'
$BackendEnv = Join-Path $BackendDir '.env'
$DuckDb = Join-Path $RepoRoot 'data\warehouse\voxmetrik.duckdb'
$VenvPython = Join-Path $BackendDir '.venv\Scripts\python.exe'

if (-not (Test-Path $BackendEnv)) {
    Write-Error "Missing apps/backend/.env — copy from .env.example and configure before starting."
    exit 1
}
if (-not (Test-Path $DuckDb)) {
    Write-Error "Missing data/warehouse/voxmetrik.duckdb — restore DEMO-RUNTIME or seed first."
    exit 1
}
if (-not (Test-Path $VenvPython)) {
    Write-Error "Missing apps/backend/.venv — run .\scripts\setup_demo.ps1 first."
    exit 1
}

New-Item -ItemType Directory -Force -Path $PidDir | Out-Null

function Test-UrlOk {
    param([string]$Url, [int]$TimeoutSec = 3)
    try {
        $resp = Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec $TimeoutSec -ErrorAction Stop
        return ($resp.StatusCode -ge 200 -and $resp.StatusCode -lt 500)
    } catch {
        return $false
    }
}

$BackendLog = Join-Path $PidDir 'backend.log'
$FrontendLog = Join-Path $PidDir 'frontend.log'
$BackendPidFile = Join-Path $PidDir 'backend.pid'
$FrontendPidFile = Join-Path $PidDir 'frontend.pid'

# Backend: cmd wrapper sets EMAIL_PROVIDER=console for the uvicorn child
$backendBat = Join-Path $PidDir 'backend_launch.cmd'
@(
    '@echo off'
    'set EMAIL_PROVIDER=console'
    "cd /d `"$BackendDir`""
    "`"$VenvPython`" -m uvicorn app.main:app --host 127.0.0.1 --port 8000 > `"$BackendLog`" 2>&1"
) | Set-Content -Path $backendBat -Encoding ASCII

$cmdProc = Start-Process -FilePath 'cmd.exe' -ArgumentList '/c', "`"$backendBat`"" -WorkingDirectory $BackendDir -PassThru -WindowStyle Hidden

$backendPid = $null
$deadline = (Get-Date).AddSeconds(20)
while ((Get-Date) -lt $deadline) {
    $conn = Get-NetTCPConnection -LocalPort 8000 -State Listen -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($conn) {
        $backendPid = [int]$conn.OwningProcess
        break
    }
    $child = Get-CimInstance Win32_Process -Filter "ParentProcessId=$($cmdProc.Id)" -ErrorAction SilentlyContinue |
        Where-Object { $_.Name -match 'python' } | Select-Object -First 1
    if ($child) { $backendPid = [int]$child.ProcessId }

    if ((Test-UrlOk 'http://127.0.0.1:8000/health') -or (Test-UrlOk 'http://127.0.0.1:8000/docs')) {
        if (-not $backendPid) { $backendPid = [int]$cmdProc.Id }
        break
    }
    Start-Sleep -Milliseconds 500
}

if (-not ((Test-UrlOk 'http://127.0.0.1:8000/health') -or (Test-UrlOk 'http://127.0.0.1:8000/docs'))) {
    Write-Error "Backend did not respond on /health or /docs within 20s. See scripts/.demo-pids/backend.log"
    exit 1
}
if (-not $backendPid) { $backendPid = [int]$cmdProc.Id }
Set-Content -Path $BackendPidFile -Value $backendPid -Encoding ASCII

# Frontend
$npmCmd = (Get-Command npm.cmd -ErrorAction SilentlyContinue)
if (-not $npmCmd) { $npmCmd = Get-Command npm -ErrorAction Stop }
$frontendBat = Join-Path $PidDir 'frontend_launch.cmd'
@(
    '@echo off'
    "cd /d `"$FrontendDir`""
    "call `"$($npmCmd.Source)`" start -- --host 127.0.0.1 --port 4200 > `"$FrontendLog`" 2>&1"
) | Set-Content -Path $frontendBat -Encoding ASCII

$feCmdProc = Start-Process -FilePath 'cmd.exe' -ArgumentList '/c', "`"$frontendBat`"" -WorkingDirectory $FrontendDir -PassThru -WindowStyle Hidden

$frontendPid = $null
$feDeadline = (Get-Date).AddSeconds(60)
while ((Get-Date) -lt $feDeadline) {
    $conn = Get-NetTCPConnection -LocalPort 4200 -State Listen -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($conn) {
        $frontendPid = [int]$conn.OwningProcess
        break
    }
    if (Test-UrlOk 'http://127.0.0.1:4200/') {
        $node = Get-Process -Name 'node' -ErrorAction SilentlyContinue | Select-Object -First 1
        if ($node) { $frontendPid = [int]$node.Id }
        break
    }
    Start-Sleep -Seconds 1
}
if (-not $frontendPid) { $frontendPid = [int]$feCmdProc.Id }
Set-Content -Path $FrontendPidFile -Value $frontendPid -Encoding ASCII

Write-Host 'http://127.0.0.1:4200'
Write-Host 'http://127.0.0.1:8000/health'
exit 0
