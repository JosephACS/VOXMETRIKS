#requires -Version 5.1
<#
.SYNOPSIS
  Stop demo processes started by start_demo.ps1 for THIS repo only.

  Session-owned launchers are only:
    backend.launcher.json  + kind launcher-backend  + executablePath == resolved venv python
    frontend.launcher.json + kind launcher-frontend + executablePath == resolved node.exe

  Backend: after PID + StartTimeUtc + executablePath validation, create
  backend.shutdown.request and wait up to 20s for graceful Uvicorn/lifespan exit
  (log must contain "VOXMETRIK_V2 shutdown complete"). Force-kill only on timeout
  and then exit 1 (runtime not healthy).

  Frontend may be force-stopped after backend handling.

  Artifact cleanup deletes only DemoArtifactNames as direct children of PidDir.
  session-artifacts.json is never trusted to expand the delete set.
#>
[CmdletBinding()]
param()

$ErrorActionPreference = 'Continue'
$RepoRoot = Split-Path -Parent $PSScriptRoot
. (Join-Path $PSScriptRoot 'demo_runtime_common.ps1')

$PidDir = Join-Path $RepoRoot 'scripts\.demo-pids'
$BackendDir = Join-Path $RepoRoot 'apps\backend'
$FrontendDir = Join-Path $RepoRoot 'apps\frontend'
$VenvPython = Join-Path $BackendDir '.venv\Scripts\python.exe'
$RepoRootLower = $RepoRoot.ToLowerInvariant()
$FrontendDirLower = $FrontendDir.ToLowerInvariant()
$VenvDirLower = (Join-Path $BackendDir '.venv').ToLowerInvariant()
$VenvPythonResolved = $null
$VenvPythonLower = $VenvPython.ToLowerInvariant()
if (Test-Path -LiteralPath $VenvPython) {
    $VenvPythonResolved = (Resolve-Path -LiteralPath $VenvPython).Path
    $VenvPythonLower = $VenvPythonResolved.ToLowerInvariant()
}
$NodeExeResolved = $null
$nodeCmd = Get-Command node.exe -ErrorAction SilentlyContinue
if ($nodeCmd) {
    $NodeExeResolved = $nodeCmd.Source
}

$script:ForeignPort = $false
$script:UnverifiableListener = $false
$script:LauncherStopFailed = $false
$script:BackendGracefulFailed = $false

# Whitelist of artifact file names this demo stack may create (never delete unknowns).
$DemoArtifactNames = @(
    'backend.launcher.json',
    'frontend.launcher.json',
    'backend.listener-note.json',
    'frontend.listener-note.json',
    'backend.shutdown.request',
    'session-artifacts.json',
    'backend.out.log',
    'backend.err.log',
    'frontend.out.log',
    'frontend.err.log',
    'backend.log',
    'frontend.log',
    'backend.json',
    'frontend.json',
    'backend.wrapper.json',
    'frontend.wrapper.json',
    'backend_launch.cmd',
    'frontend_launch.cmd'
)

function Read-MetaRecord {
    param([string]$Path)
    if (-not (Test-Path -LiteralPath $Path)) { return $null }
    try {
        $raw = Get-Content -LiteralPath $Path -Raw -ErrorAction Stop
        if ([string]::IsNullOrWhiteSpace($raw)) { return $null }
        return ($raw | ConvertFrom-Json)
    } catch {
        Write-Warning "Invalid metadata at $Path"
        return $null
    }
}

function Test-PersistedLauncherMetaAllowed {
    param(
        [string]$FileName,
        [object]$Meta
    )
    if (-not $Meta) { return $false }
    $sessionOwned = $false
    if ($Meta.PSObject.Properties.Name -contains 'sessionOwned') {
        $sessionOwned = [bool]$Meta.sessionOwned
    }
    if (-not $sessionOwned) { return $false }

    $kind = [string]$Meta.kind
    $metaExe = [string]$Meta.executablePath

    if ($FileName -eq 'backend.launcher.json') {
        if ($kind -ne 'launcher-backend') { return $false }
        if ([string]::IsNullOrWhiteSpace($VenvPythonResolved)) { return $false }
        return (Test-DemoExecutablePathEquals -Left $metaExe -Right $VenvPythonResolved)
    }
    if ($FileName -eq 'frontend.launcher.json') {
        if ($kind -ne 'launcher-frontend') { return $false }
        if ([string]::IsNullOrWhiteSpace($NodeExeResolved)) { return $false }
        return (Test-DemoExecutablePathEquals -Left $metaExe -Right $NodeExeResolved)
    }
    return $false
}

function Stop-SessionOwnedBackendGracefulFromMeta {
    param([string]$Path)
    $leaf = [IO.Path]::GetFileName($Path)
    if (-not [string]::Equals($leaf, 'backend.launcher.json', [StringComparison]::OrdinalIgnoreCase)) {
        return
    }

    $meta = Read-MetaRecord -Path $Path
    if (-not $meta) { return }

    if (-not (Test-PersistedLauncherMetaAllowed -FileName 'backend.launcher.json' -Meta $meta)) {
        Write-Warning 'Refusing session-owned stop from backend.launcher.json: kind/executablePath not an allowed demo launcher (left intact).'
        return
    }

    $pidVal = 0
    if (-not [int]::TryParse([string]$meta.pid, [ref]$pidVal)) {
        Write-Warning "Invalid pid in $Path"
        return
    }

    $handle = Get-DemoProcessHandleInfo -ProcessId $pidVal
    if (-not $handle) {
        Write-Host "PID $pidVal not running - (backend.launcher.json)"
        # Still require shutdown marker if port is free from a prior graceful exit.
        if ((-not (Get-PortListenerPid -Port 8000)) -and (Test-DemoBackendShutdownCompleteInLogs -PidDir $PidDir)) {
            Write-Host 'Backend already stopped with VOXMETRIK_V2 shutdown complete.'
            return
        }
        return
    }

    $record = [pscustomobject]@{
        Pid            = $pidVal
        StartTimeUtc   = [string]$meta.startTimeUtc
        ExecutablePath = [string]$meta.executablePath
        Kind           = [string]$meta.kind
    }
    if (-not (Test-SessionOwnedHandleMatch -HandleInfo $handle -Record $record)) {
        Write-Warning ("Refusing to stop PID {0} from backend.launcher.json: handle metadata mismatch (left intact)." -f $pidVal)
        return
    }

    if (-not (Test-DemoExecutablePathEquals -Left ([string]$handle.ExecutablePath) -Right $VenvPythonResolved)) {
        Write-Warning ("Refusing to stop PID {0} from backend.launcher.json: live executablePath is not the expected demo launcher (left intact)." -f $pidVal)
        return
    }

    try {
        $gr = Stop-DemoBackendGracefulOrForce -ProcessId ([int]$handle.Pid) -PidDir $PidDir -TimeoutSec 20
        if ($gr.Ok) {
            Write-Host ("Stopped PID {0} (launcher-backend) graceful - VOXMETRIK_V2 shutdown complete" -f $handle.Pid)
        } else {
            $script:BackendGracefulFailed = $true
            $script:LauncherStopFailed = $true
            Write-Warning ("Backend PID {0} did not shut down gracefully ({1}). Forced={2}. Runtime is NOT healthy." -f $handle.Pid, $gr.Detail, $gr.Forced)
        }
    } catch {
        $script:LauncherStopFailed = $true
        $script:BackendGracefulFailed = $true
        Write-Warning "Could not stop backend PID $($handle.Pid): $_"
    }
}

function Stop-SessionOwnedFrontendFromMeta {
    param([string]$Path)
    $leaf = [IO.Path]::GetFileName($Path)
    if (-not [string]::Equals($leaf, 'frontend.launcher.json', [StringComparison]::OrdinalIgnoreCase)) {
        return
    }

    $meta = Read-MetaRecord -Path $Path
    if (-not $meta) { return }

    if (-not (Test-PersistedLauncherMetaAllowed -FileName 'frontend.launcher.json' -Meta $meta)) {
        Write-Warning 'Refusing session-owned stop from frontend.launcher.json: kind/executablePath not an allowed demo launcher (left intact).'
        return
    }

    $pidVal = 0
    if (-not [int]::TryParse([string]$meta.pid, [ref]$pidVal)) {
        Write-Warning "Invalid pid in $Path"
        return
    }

    $handle = Get-DemoProcessHandleInfo -ProcessId $pidVal
    if (-not $handle) {
        Write-Host "PID $pidVal not running - (frontend.launcher.json)"
        return
    }

    $record = [pscustomobject]@{
        Pid            = $pidVal
        StartTimeUtc   = [string]$meta.startTimeUtc
        ExecutablePath = [string]$meta.executablePath
        Kind           = [string]$meta.kind
    }
    if (-not (Test-SessionOwnedHandleMatch -HandleInfo $handle -Record $record)) {
        Write-Warning ("Refusing to stop PID {0} from frontend.launcher.json: handle metadata mismatch (left intact)." -f $pidVal)
        return
    }

    if (-not (Test-DemoExecutablePathEquals -Left ([string]$handle.ExecutablePath) -Right $NodeExeResolved)) {
        Write-Warning ("Refusing to stop PID {0} from frontend.launcher.json: live executablePath is not the expected demo launcher (left intact)." -f $pidVal)
        return
    }

    try {
        $ok = Stop-DemoVerifiedLauncher -ProcessId ([int]$handle.Pid)
        if ($ok) {
            Write-Host ("Stopped PID {0} (launcher-frontend) from frontend.launcher.json" -f $handle.Pid)
        } else {
            $script:LauncherStopFailed = $true
            Write-Warning ("Failed to stop verified launcher PID {0} from frontend.launcher.json" -f $handle.Pid)
        }
    } catch {
        $script:LauncherStopFailed = $true
        Write-Warning "Could not stop PID $($handle.Pid): $_"
    }
}

function Stop-StrictPortListenerIfOwned {
    param(
        [int]$Port,
        [ValidateSet('backend', 'frontend')]
        [string]$Kind
    )
    $listenerPid = Get-PortListenerPid -Port $Port
    if (-not $listenerPid) { return }

    $handle = Get-DemoProcessHandleInfo -ProcessId $listenerPid
    $wmi = Get-DemoProcessWmiInfo -ProcessId $listenerPid
    if (-not $handle -or -not $wmi -or [string]::IsNullOrWhiteSpace([string]$wmi.CommandLine)) {
        $script:ForeignPort = $true
        $script:UnverifiableListener = $true
        Write-Warning ("Port {0} PID {1}: WMI/commandLine unavailable - refusing stop (left intact)." -f $Port, $listenerPid)
        return
    }

    $ok = Test-StrictPortWorkerIdentity -WmiInfo $wmi -HandleInfo $handle -Kind $Kind `
        -RepoRootLower $RepoRootLower -VenvDirLower $VenvDirLower `
        -VenvPythonLower $VenvPythonLower -FrontendDirLower $FrontendDirLower
    if (-not $ok) {
        $script:ForeignPort = $true
        Write-Warning ("Port {0} is in use by PID {1} outside this repo demo stack - left running." -f $Port, $listenerPid)
        return
    }

    try {
        Stop-Process -Id $handle.Pid -Force -ErrorAction Stop
        Write-Host ("Stopped PID {0} ({1}) from port:{2}" -f $handle.Pid, $Kind, $Port)
    } catch {
        Write-Warning "Could not stop PID $($handle.Pid): $_"
    }
}

function Clear-WhitelistedDemoArtifacts {
    if (-not (Test-Path -LiteralPath $PidDir)) { return }

    # Never trust session-artifacts.json to expand the delete set.
    $toDelete = @()
    foreach ($name in $DemoArtifactNames) {
        if ([string]::IsNullOrWhiteSpace($name)) { continue }
        if ($name -match '[\\/]') { continue }
        $p = Join-Path $PidDir $name
        if (Test-Path -LiteralPath $p) { $toDelete += $p }
    }
    Clear-DemoSessionArtifacts -ArtifactPaths $toDelete -PidDir $PidDir
}

# 1) Backend graceful first, then frontend force.
if (Test-Path -LiteralPath $PidDir) {
    $backendMetaPath = Join-Path $PidDir 'backend.launcher.json'
    $frontendMetaPath = Join-Path $PidDir 'frontend.launcher.json'
    if (Test-Path -LiteralPath $backendMetaPath) {
        Stop-SessionOwnedBackendGracefulFromMeta -Path $backendMetaPath
    }
    if (Test-Path -LiteralPath $frontendMetaPath) {
        Stop-SessionOwnedFrontendFromMeta -Path $frontendMetaPath
    }
} else {
    Write-Host 'No scripts/.demo-pids metadata - will still inspect ports 8000/4200 for owned listeners.'
}

Start-Sleep -Milliseconds 600

# 2) Port reclaim only with strict WMI identity (legacy / leftover listeners).
# Backend port reclaim after failed graceful still uses force on verified workers only.
Stop-StrictPortListenerIfOwned -Port 8000 -Kind 'backend'
Stop-StrictPortListenerIfOwned -Port 4200 -Kind 'frontend'

Start-Sleep -Milliseconds 400

$stillBusy = @()
foreach ($port in @(8000, 4200)) {
    if (Get-PortListenerPid -Port $port) {
        $stillBusy += $port
    }
}

if ($stillBusy.Count -gt 0 -or $script:ForeignPort -or $script:UnverifiableListener -or $script:LauncherStopFailed -or $script:BackendGracefulFailed) {
    if ($script:BackendGracefulFailed) {
        Write-Warning 'Backend closure was not graceful (timeout/force). Do not treat the demo runtime as healthy.'
    }
    if ($script:UnverifiableListener) {
        Write-Warning 'A listener remained after stopping the session launcher but could not be verified (WMI/commandLine unavailable). Process left intact.'
    }
    if ($script:LauncherStopFailed) {
        Write-Warning 'A verified session launcher could not be fully stopped.'
    }
    Write-Warning ("Ports not fully free: {0}" -f (($stillBusy -join ', ')))
    Write-Host 'stop_demo incomplete'
    Clear-WhitelistedDemoArtifacts
    exit 1
}

Clear-WhitelistedDemoArtifacts
Write-Host 'Ports 8000 and 4200 are free.'
Write-Host 'stop_demo complete'
exit 0
