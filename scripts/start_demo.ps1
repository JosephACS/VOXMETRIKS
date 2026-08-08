#requires -Version 5.1
<#
.SYNOPSIS
  Start local demo backend + frontend. Prints only public URLs (no secrets).
  Exits 0 only when /health is a VOXMETRIKS health JSON and Angular host returns HTTP 200.
  Never mutates DuckDB sidecars; never stops foreign listeners.

  Launches processes directly (venv python / node+ng.js). Session ownership uses
  Process handle identity (PID + StartTimeUtc + executablePath), not WMI.
#>
[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$RepoRoot = Split-Path -Parent $PSScriptRoot
. (Join-Path $PSScriptRoot 'demo_runtime_common.ps1')

$PidDir = Join-Path $RepoRoot 'scripts\.demo-pids'
$BackendDir = Join-Path $RepoRoot 'apps\backend'
$FrontendDir = Join-Path $RepoRoot 'apps\frontend'
$BackendEnv = Join-Path $BackendDir '.env'
$DuckDb = Join-Path $RepoRoot 'data\warehouse\voxmetrik.duckdb'
$VenvPython = Join-Path $BackendDir '.venv\Scripts\python.exe'
$NgJs = Join-Path $FrontendDir 'node_modules\@angular\cli\bin\ng.js'
$NodeExe = $null

if (-not (Test-Path -LiteralPath $BackendEnv)) {
    Write-Error 'Missing apps/backend/.env - copy from .env.example and configure before starting.'
    exit 1
}
if (-not (Test-Path -LiteralPath $DuckDb)) {
    Write-Error 'Missing data/warehouse/voxmetrik.duckdb - restore DEMO-RUNTIME or seed first.'
    exit 1
}
if (-not (Test-Path -LiteralPath $VenvPython)) {
    Write-Error 'Missing apps/backend/.venv - run .\scripts\setup_demo.ps1 first.'
    exit 1
}
if (-not (Test-Path -LiteralPath $NgJs)) {
    Write-Error 'Missing apps/frontend/node_modules/@angular/cli/bin/ng.js - run npm install in apps/frontend.'
    exit 1
}
$nodeCmd = Get-Command node.exe -ErrorAction SilentlyContinue
if (-not $nodeCmd) {
    Write-Error 'node.exe not found on PATH.'
    exit 1
}
$NodeExe = $nodeCmd.Source
$VenvPythonResolved = (Resolve-Path -LiteralPath $VenvPython).Path
$VenvPythonLower = $VenvPythonResolved.ToLowerInvariant()
$NgJsResolved = (Resolve-Path -LiteralPath $NgJs).Path

foreach ($port in @(8000, 4200)) {
    $busyPid = Get-PortListenerPid -Port $port
    if ($busyPid) {
        Write-Host "ERROR: Port $port is already in use by PID $busyPid."
        Write-Host 'If that process belongs to a previous VOXMETRIKS demo, run: .\scripts\stop_demo.ps1'
        Write-Host 'Otherwise free the port manually. start_demo will not stop foreign processes.'
        exit 1
    }
}

New-Item -ItemType Directory -Force -Path $PidDir | Out-Null
$script:Owned = New-Object 'System.Collections.Generic.List[object]'
$script:SessionArtifacts = New-Object 'System.Collections.Generic.List[string]'

function Register-SessionArtifact {
    param([string]$Path)
    if ([string]::IsNullOrWhiteSpace($Path)) { return }
    if (-not $script:SessionArtifacts.Contains($Path)) {
        $script:SessionArtifacts.Add($Path) | Out-Null
    }
}

function Save-SessionOwnedLauncher {
    param(
        [int]$ProcessId,
        [ValidateSet('launcher-backend', 'launcher-frontend')]
        [string]$Kind,
        [string]$ExecutablePath,
        [string[]]$ExpectedArgs,
        [string]$MetaPath
    )
    $handle = Get-DemoProcessHandleInfo -ProcessId $ProcessId
    if (-not $handle) {
        throw ("Cannot record owned {0}: process handle identity unavailable for PID {1}." -f $Kind, $ProcessId)
    }
    # Prefer the executable we intentionally launched when Path matches.
    $exe = $ExecutablePath
    if (-not [string]::IsNullOrWhiteSpace([string]$handle.ExecutablePath)) {
        $exe = [string]$handle.ExecutablePath
    }
    $payload = [ordered]@{
        pid              = [int]$handle.Pid
        kind             = $Kind
        name             = [string]$handle.Name
        startTimeUtc     = [string]$handle.StartTimeUtc
        executablePath   = $exe
        expectedArgs     = @($ExpectedArgs)
        sessionOwned     = $true
        requireWmiToStop = $false
    }
    ($payload | ConvertTo-Json -Compress) | Set-Content -LiteralPath $MetaPath -Encoding ASCII
    Register-SessionArtifact -Path $MetaPath
    $script:Owned.Add([pscustomobject]@{
        Pid            = [int]$handle.Pid
        Kind           = $Kind
        StartTimeUtc   = [string]$handle.StartTimeUtc
        ExecutablePath = $exe
        ExpectedArgs   = @($ExpectedArgs)
        MetaPath       = $MetaPath
        SessionOwned   = $true
    }) | Out-Null
}

function Write-SessionArtifactsManifest {
    $manifest = Join-Path $PidDir 'session-artifacts.json'
    $paths = @($script:SessionArtifacts.ToArray())
    (@{ artifacts = $paths } | ConvertTo-Json -Compress) | Set-Content -LiteralPath $manifest -Encoding ASCII
    Register-SessionArtifact -Path $manifest
    # Re-write so manifest includes itself.
    (@{ artifacts = @($script:SessionArtifacts.ToArray()) } | ConvertTo-Json -Compress) | Set-Content -LiteralPath $manifest -Encoding ASCII
}

function Stop-OwnedSessionProcesses {
    Stop-DemoSessionOwnedRecords -OwnedList $script:Owned
    if ($null -ne $script:Owned) { $script:Owned.Clear() }
    $arts = @()
    if ($null -ne $script:SessionArtifacts -and $script:SessionArtifacts.Count -gt 0) {
        $arts = @($script:SessionArtifacts.ToArray())
    }
    Clear-DemoSessionArtifacts -ArtifactPaths $arts -PidDir $PidDir
    if ($null -ne $script:SessionArtifacts) { $script:SessionArtifacts.Clear() }
}

function Wait-BackendReady {
    param(
        [int]$LauncherPid,
        [int]$TimeoutSec = 60
    )
    $deadline = (Get-Date).AddSeconds($TimeoutSec)
    while ((Get-Date) -lt $deadline) {
        if (Test-VoxmetriksHealthResponse) {
            $listenerPid = Get-PortListenerPid -Port 8000
            return [pscustomobject]@{
                Ok          = $true
                ListenerPid = $listenerPid
            }
        }
        if (-not (Test-DemoProcessRunning -ProcessId $LauncherPid)) {
            return [pscustomobject]@{ Ok = $false; ListenerPid = $null; Reason = 'launcher-exited' }
        }
        Start-Sleep -Milliseconds 500
    }
    return [pscustomobject]@{ Ok = $false; ListenerPid = (Get-PortListenerPid -Port 8000); Reason = 'timeout' }
}

function Wait-FrontendReady {
    param(
        [int]$LauncherPid,
        [int]$TimeoutSec = 120
    )
    $deadline = (Get-Date).AddSeconds($TimeoutSec)
    while ((Get-Date) -lt $deadline) {
        if (Test-DemoHttpStatus200 'http://127.0.0.1:4200/') {
            $listenerPid = Get-PortListenerPid -Port 4200
            return [pscustomobject]@{
                Ok          = $true
                ListenerPid = $listenerPid
            }
        }
        if (-not (Test-DemoProcessRunning -ProcessId $LauncherPid)) {
            return [pscustomobject]@{ Ok = $false; ListenerPid = $null; Reason = 'launcher-exited' }
        }
        Start-Sleep -Milliseconds 500
    }
    return [pscustomobject]@{ Ok = $false; ListenerPid = (Get-PortListenerPid -Port 4200); Reason = 'timeout' }
}

$BackendLog = Join-Path $PidDir 'backend.out.log'
$BackendErr = Join-Path $PidDir 'backend.err.log'
$FrontendLog = Join-Path $PidDir 'frontend.out.log'
$FrontendErr = Join-Path $PidDir 'frontend.err.log'
$BackendMeta = Join-Path $PidDir 'backend.launcher.json'
$FrontendMeta = Join-Path $PidDir 'frontend.launcher.json'
$BackendListenerNote = Join-Path $PidDir 'backend.listener-note.json'
$FrontendListenerNote = Join-Path $PidDir 'frontend.listener-note.json'

try {
    Register-SessionArtifact -Path $BackendLog
    Register-SessionArtifact -Path $BackendErr
    Register-SessionArtifact -Path $FrontendLog
    Register-SessionArtifact -Path $FrontendErr

    $backendArgs = @('-m', 'uvicorn', 'app.main:app', '--host', '127.0.0.1', '--port', '8000')
    $envKeys = @('EMAIL_PROVIDER', 'SKIP_SYSTEM_BOOT', 'JOBS_ENABLED', 'RUN_ETL_ON_BOOT')
    $envSaved = @{}
    foreach ($k in $envKeys) {
        $envSaved[$k] = [Environment]::GetEnvironmentVariable($k, 'Process')
    }
    try {
        $env:EMAIL_PROVIDER = 'console'
        $env:SKIP_SYSTEM_BOOT = '1'
        $env:JOBS_ENABLED = 'false'
        $env:RUN_ETL_ON_BOOT = 'never'

        $backendProc = Start-DemoDetachedProcess `
            -FilePath $VenvPythonResolved `
            -ArgumentList $backendArgs `
            -WorkingDirectory $BackendDir `
            -StdoutLog $BackendLog `
            -StderrLog $BackendErr
    } finally {
        foreach ($k in $envKeys) {
            $prev = $envSaved[$k]
            if ($null -eq $prev -or $prev -eq '') {
                Remove-Item -Path ("Env:{0}" -f $k) -ErrorAction SilentlyContinue
            } else {
                [Environment]::SetEnvironmentVariable($k, [string]$prev, 'Process')
            }
        }
    }

    Start-Sleep -Milliseconds 200
    if (-not $backendProc -or -not (Test-DemoProcessRunning -ProcessId ([int]$backendProc.Id))) {
        throw 'Backend launcher exited immediately after Start-Process.'
    }
    Save-SessionOwnedLauncher -ProcessId ([int]$backendProc.Id) -Kind 'launcher-backend' `
        -ExecutablePath $VenvPythonResolved -ExpectedArgs $backendArgs -MetaPath $BackendMeta

    $beReady = Wait-BackendReady -LauncherPid ([int]$backendProc.Id) -TimeoutSec 60
    if (-not $beReady.Ok) {
        Write-Host ("ERROR: Backend did not expose VOXMETRIKS /health within 60s ({0})." -f $beReady.Reason)
        Show-DemoLogTail -StdoutLog $BackendLog -StderrLog $BackendErr
        Stop-OwnedSessionProcesses
        exit 1
    }

    # Associate listener observed during startup (port was free before launch).
    if ($beReady.ListenerPid -and ([int]$beReady.ListenerPid -ne [int]$backendProc.Id)) {
        $note = [ordered]@{
            kind                 = 'listener-association'
            port                 = 8000
            launcherPid          = [int]$backendProc.Id
            listenerPid          = [int]$beReady.ListenerPid
            associatedAtUtc      = (Get-Date).ToUniversalTime().ToString('o')
            note                 = 'Listener PID differs from launcher (common on Windows venv). Stop kills launcher tree first; unverifiable leftover listener is an error.'
            sessionOwnedListener = $false
        }
        ($note | ConvertTo-Json -Compress) | Set-Content -LiteralPath $BackendListenerNote -Encoding ASCII
        Register-SessionArtifact -Path $BackendListenerNote
    }

    $frontendArgs = @(
        $NgJsResolved,
        'serve',
        '--host', '127.0.0.1',
        '--port', '4200'
    )
    $frontendProc = Start-DemoDetachedProcess `
        -FilePath $NodeExe `
        -ArgumentList $frontendArgs `
        -WorkingDirectory $FrontendDir `
        -StdoutLog $FrontendLog `
        -StderrLog $FrontendErr

    Start-Sleep -Milliseconds 200
    if (-not $frontendProc -or -not (Test-DemoProcessRunning -ProcessId ([int]$frontendProc.Id))) {
        throw 'Frontend launcher exited immediately after Start-Process.'
    }
    Save-SessionOwnedLauncher -ProcessId ([int]$frontendProc.Id) -Kind 'launcher-frontend' `
        -ExecutablePath $NodeExe -ExpectedArgs $frontendArgs -MetaPath $FrontendMeta

    $feReady = Wait-FrontendReady -LauncherPid ([int]$frontendProc.Id) -TimeoutSec 120
    if (-not $feReady.Ok) {
        Write-Host ("ERROR: Frontend did not return HTTP 200 on http://127.0.0.1:4200/ within 120s ({0})." -f $feReady.Reason)
        Show-DemoLogTail -StdoutLog $FrontendLog -StderrLog $FrontendErr
        Stop-OwnedSessionProcesses
        exit 1
    }

    if ($feReady.ListenerPid -and ([int]$feReady.ListenerPid -ne [int]$frontendProc.Id)) {
        $note = [ordered]@{
            kind                 = 'listener-association'
            port                 = 4200
            launcherPid          = [int]$frontendProc.Id
            listenerPid          = [int]$feReady.ListenerPid
            associatedAtUtc      = (Get-Date).ToUniversalTime().ToString('o')
            sessionOwnedListener = $false
        }
        ($note | ConvertTo-Json -Compress) | Set-Content -LiteralPath $FrontendListenerNote -Encoding ASCII
        Register-SessionArtifact -Path $FrontendListenerNote
    }

    if (-not (Test-VoxmetriksHealthResponse)) {
        Write-Host 'ERROR: Backend /health is not a VOXMETRIKS health response after frontend start.'
        Stop-OwnedSessionProcesses
        exit 1
    }
    if (-not (Test-DemoHttpStatus200 'http://127.0.0.1:4200/')) {
        Write-Host 'ERROR: Frontend / is not HTTP 200 after startup.'
        Stop-OwnedSessionProcesses
        exit 1
    }

    Write-SessionArtifactsManifest

    Write-Host 'http://127.0.0.1:4200'
    Write-Host 'http://127.0.0.1:8000/health'
    exit 0
} catch {
    Write-Host ("ERROR: start_demo failed: {0}" -f $_.Exception.Message)
    Stop-OwnedSessionProcesses
    exit 1
}
