#requires -Version 5.1
<#
.SYNOPSIS
  Stop demo processes started by start_demo.ps1 for THIS repo only.

  Session-owned launchers are only:
    backend.launcher.json  + kind launcher-backend  + executablePath == resolved venv python
    frontend.launcher.json + kind launcher-frontend + executablePath == resolved node.exe

  Those are stopped via Process handle match (PID + StartTimeUtc + executablePath)
  without requiring WMI (taskkill /T, then Stop-Process fallback on that PID only).

  Port-discovered arbitrary processes still require strict WMI commandLine validation.
  Missing WMI/commandLine => refuse stop (process left intact).

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

# Whitelist of artifact file names this demo stack may create (never delete unknowns).
$DemoArtifactNames = @(
    'backend.launcher.json',
    'frontend.launcher.json',
    'backend.listener-note.json',
    'frontend.listener-note.json',
    'backend.out.log',
    'backend.err.log',
    'frontend.out.log',
    'frontend.err.log',
    'session-artifacts.json',
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

function Stop-SessionOwnedLauncherFromMeta {
    param(
        [string]$Path,
        [string]$ExpectedFileName
    )
    $leaf = [IO.Path]::GetFileName($Path)
    if (-not [string]::Equals($leaf, $ExpectedFileName, [StringComparison]::OrdinalIgnoreCase)) {
        return
    }

    $meta = Read-MetaRecord -Path $Path
    if (-not $meta) { return }

    if (-not (Test-PersistedLauncherMetaAllowed -FileName $ExpectedFileName -Meta $meta)) {
        Write-Warning ("Refusing session-owned stop from {0}: kind/executablePath not an allowed demo launcher (left intact)." -f $ExpectedFileName)
        return
    }

    $pidVal = 0
    if (-not [int]::TryParse([string]$meta.pid, [ref]$pidVal)) {
        Write-Warning "Invalid pid in $Path"
        return
    }

    $handle = Get-DemoProcessHandleInfo -ProcessId $pidVal
    if (-not $handle) {
        Write-Host "PID $pidVal not running - ($ExpectedFileName)"
        return
    }

    $record = [pscustomobject]@{
        Pid            = $pidVal
        StartTimeUtc   = [string]$meta.startTimeUtc
        ExecutablePath = [string]$meta.executablePath
        Kind           = [string]$meta.kind
    }
    if (-not (Test-SessionOwnedHandleMatch -HandleInfo $handle -Record $record)) {
        Write-Warning ("Refusing to stop PID {0} from {1}: handle metadata mismatch (left intact)." -f $pidVal, $ExpectedFileName)
        return
    }

    # Live exe must also equal the expected resolved demo executable.
    $expectedExe = if ($ExpectedFileName -eq 'backend.launcher.json') { $VenvPythonResolved } else { $NodeExeResolved }
    if (-not (Test-DemoExecutablePathEquals -Left ([string]$handle.ExecutablePath) -Right $expectedExe)) {
        Write-Warning ("Refusing to stop PID {0} from {1}: live executablePath is not the expected demo launcher (left intact)." -f $pidVal, $ExpectedFileName)
        return
    }

    try {
        $ok = Stop-DemoVerifiedLauncher -ProcessId ([int]$handle.Pid)
        if ($ok) {
            Write-Host ("Stopped PID {0} ({1}) from {2}" -f $handle.Pid, $meta.kind, $ExpectedFileName)
        } else {
            $script:LauncherStopFailed = $true
            Write-Warning ("Failed to stop verified launcher PID {0} from {1}" -f $handle.Pid, $ExpectedFileName)
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

# 1) Stop only the two allowed launcher metadata files (handle identity; no WMI).
if (Test-Path -LiteralPath $PidDir) {
    $backendMetaPath = Join-Path $PidDir 'backend.launcher.json'
    $frontendMetaPath = Join-Path $PidDir 'frontend.launcher.json'
    if (Test-Path -LiteralPath $backendMetaPath) {
        Stop-SessionOwnedLauncherFromMeta -Path $backendMetaPath -ExpectedFileName 'backend.launcher.json'
    }
    if (Test-Path -LiteralPath $frontendMetaPath) {
        Stop-SessionOwnedLauncherFromMeta -Path $frontendMetaPath -ExpectedFileName 'frontend.launcher.json'
    }
} else {
    Write-Host 'No scripts/.demo-pids metadata - will still inspect ports 8000/4200 for owned listeners.'
}

Start-Sleep -Milliseconds 600

# 2) Port reclaim only with strict WMI identity (legacy / leftover listeners).
Stop-StrictPortListenerIfOwned -Port 8000 -Kind 'backend'
Stop-StrictPortListenerIfOwned -Port 4200 -Kind 'frontend'

Start-Sleep -Milliseconds 400

$stillBusy = @()
foreach ($port in @(8000, 4200)) {
    if (Get-PortListenerPid -Port $port) {
        $stillBusy += $port
    }
}

if ($stillBusy.Count -gt 0 -or $script:ForeignPort -or $script:UnverifiableListener -or $script:LauncherStopFailed) {
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
