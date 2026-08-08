#requires -Version 5.1
<#
.SYNOPSIS
  Start local demo backend + frontend. Prints only public URLs (no secrets).
  Exits 0 only when both /health and the Angular host respond with HTTP 200.
  Never mutates DuckDB sidecars; never stops foreign listeners.
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
$RepoRootLower = $RepoRoot.ToLowerInvariant()
$BackendDirLower = $BackendDir.ToLowerInvariant()
$FrontendDirLower = $FrontendDir.ToLowerInvariant()
$VenvDirLower = (Join-Path $BackendDir '.venv').ToLowerInvariant()
$PidDirLower = $PidDir.ToLowerInvariant()

if (-not (Test-Path $BackendEnv)) {
    Write-Error 'Missing apps/backend/.env - copy from .env.example and configure before starting.'
    exit 1
}
if (-not (Test-Path $DuckDb)) {
    Write-Error 'Missing data/warehouse/voxmetrik.duckdb - restore DEMO-RUNTIME or seed first.'
    exit 1
}
if (-not (Test-Path $VenvPython)) {
    Write-Error 'Missing apps/backend/.venv - run .\scripts\setup_demo.ps1 first.'
    exit 1
}
$VenvPythonLower = (Resolve-Path -LiteralPath $VenvPython).Path.ToLowerInvariant()

function Get-PortListenerPid {
    param([int]$Port)
    $conn = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue |
        Select-Object -First 1
    if ($conn -and $conn.OwningProcess) {
        return [int]$conn.OwningProcess
    }
    return $null
}

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

function Test-HttpStatus200 {
    param(
        [string]$Url,
        [int]$TimeoutSec = 3
    )
    try {
        $resp = Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec $TimeoutSec -ErrorAction Stop
        return ($resp.StatusCode -eq 200)
    } catch {
        return $false
    }
}

function Normalize-IdentityText {
    param([string]$Value)
    if ($null -eq $Value) { return '' }
    $t = $Value.Trim().ToLowerInvariant()
    $t = $t -replace '/', '\'
    $t = $t -replace '\s+', ' '
    return $t
}

function Get-ProcessSnapshot {
    param([int]$ProcessId)
    if ($ProcessId -le 0) { return $null }
    $proc = Get-Process -Id $ProcessId -ErrorAction SilentlyContinue
    if (-not $proc) { return $null }
    $wmi = Get-CimInstance Win32_Process -Filter "ProcessId=$ProcessId" -ErrorAction SilentlyContinue
    $cmd = ''
    $exe = ''
    $parent = 0
    if ($wmi) {
        if ($wmi.CommandLine) { $cmd = [string]$wmi.CommandLine }
        if ($wmi.ExecutablePath) { $exe = [string]$wmi.ExecutablePath }
        if ($wmi.ParentProcessId) { $parent = [int]$wmi.ParentProcessId }
    }
    $startUtc = $null
    if ($proc.StartTime) {
        $startUtc = $proc.StartTime.ToUniversalTime().ToString('o')
    }
    return [pscustomobject]@{
        Pid             = $ProcessId
        Name            = $proc.ProcessName
        StartTimeUtc    = $startUtc
        CommandLine     = $cmd
        ExecutablePath  = $exe
        ParentProcessId = $parent
    }
}

function Test-PathMatch {
    param(
        [string]$Candidate,
        [string]$ExpectedLower
    )
    if ([string]::IsNullOrWhiteSpace($Candidate) -or [string]::IsNullOrWhiteSpace($ExpectedLower)) {
        return $false
    }
    return (Normalize-IdentityText $Candidate).Contains((Normalize-IdentityText $ExpectedLower))
}

function Test-IsDiscoverableDemoWorker {
    <#
      Discovery-only (under a verified wrapper). Requires real commandLine.
      Parent relationship may assist discovery; it never alone authorizes a stop.
    #>
    param(
        [object]$Snap,
        [ValidateSet('backend', 'frontend')]
        [string]$Kind,
        [int]$ExpectedParentPid = 0
    )
    if (-not $Snap) { return $false }
    $cmd = [string]$Snap.CommandLine
    $exe = [string]$Snap.ExecutablePath
    $name = ([string]$Snap.Name).ToLowerInvariant()
    if ([string]::IsNullOrWhiteSpace($cmd)) { return $false }

    if ($Kind -eq 'backend') {
        if ($name -notmatch '^(python|pythonw)$') { return $false }
        $exeInVenv = Test-PathMatch $exe $VenvDirLower
        $cmdInVenv = (Test-PathMatch $cmd $VenvPythonLower) -or (Test-PathMatch $cmd $VenvDirLower)
        if (-not ($exeInVenv -or $cmdInVenv)) { return $false }
        if ($cmd -notmatch 'uvicorn') { return $false }
        if ($cmd -notmatch 'app\.main') { return $false }
        if (-not (Test-PathMatch $cmd $RepoRootLower)) { return $false }
        if ($ExpectedParentPid -gt 0 -and [int]$Snap.ParentProcessId -ne $ExpectedParentPid) {
            # Still accept if full cmdline proves ownership (deeper descendant).
            return $true
        }
        return $true
    }

    if ($Kind -eq 'frontend') {
        if ($name -ne 'node') { return $false }
        if (-not (Test-PathMatch $cmd $FrontendDirLower)) { return $false }
        if ($cmd -notmatch 'ng serve|ng\.js|@angular[/\\]cli') { return $false }
        return $true
    }
    return $false
}

function Test-IsOwnedWrapper {
    param(
        [object]$Snap,
        [ValidateSet('wrapper-backend', 'wrapper-frontend')]
        [string]$Kind
    )
    if (-not $Snap) { return $false }
    $cmd = [string]$Snap.CommandLine
    $name = ([string]$Snap.Name).ToLowerInvariant()
    if ($name -ne 'cmd') { return $false }
    if ([string]::IsNullOrWhiteSpace($cmd)) { return $false }
    if ($Kind -eq 'wrapper-backend') {
        return (Test-PathMatch $cmd ($PidDirLower + '\backend_launch.cmd'))
    }
    return (Test-PathMatch $cmd ($PidDirLower + '\frontend_launch.cmd'))
}

function Save-OwnedMeta {
    param(
        [object]$Snap,
        [string]$Kind,
        [string]$MetaPath
    )
    $cmd = [string]$Snap.CommandLine
    $exe = [string]$Snap.ExecutablePath
    if ([string]::IsNullOrWhiteSpace($cmd) -or [string]::IsNullOrWhiteSpace($exe)) {
        throw ("Cannot record owned {0} PID {1}: commandLine/executablePath unavailable." -f $Kind, $Snap.Pid)
    }
    if ([string]::IsNullOrWhiteSpace([string]$Snap.StartTimeUtc)) {
        throw ("Cannot record owned {0} PID {1}: startTimeUtc unavailable." -f $Kind, $Snap.Pid)
    }
    $payload = [ordered]@{
        pid             = [int]$Snap.Pid
        kind            = $Kind
        name            = [string]$Snap.Name
        startTimeUtc    = [string]$Snap.StartTimeUtc
        commandLine     = $cmd
        executablePath  = $exe
        parentProcessId = [int]$Snap.ParentProcessId
    }
    ($payload | ConvertTo-Json -Compress) | Set-Content -Path $MetaPath -Encoding ASCII
    $script:Owned.Add([pscustomobject]@{
        Pid            = [int]$Snap.Pid
        Kind           = $Kind
        StartTimeUtc   = [string]$Snap.StartTimeUtc
        CommandLine    = $cmd
        ExecutablePath = $exe
        MetaPath       = $MetaPath
    }) | Out-Null
}

function Test-SnapMatchesOwnedRecord {
    param(
        [object]$Snap,
        [object]$Record
    )
    if (-not $Snap -or -not $Record) { return $false }
    if ([int]$Snap.Pid -ne [int]$Record.Pid) { return $false }
    if ([string]$Snap.StartTimeUtc -ne [string]$Record.StartTimeUtc) { return $false }

    $liveCmd = Normalize-IdentityText ([string]$Snap.CommandLine)
    $liveExe = Normalize-IdentityText ([string]$Snap.ExecutablePath)
    $metaCmd = Normalize-IdentityText ([string]$Record.CommandLine)
    $metaExe = Normalize-IdentityText ([string]$Record.ExecutablePath)

    if ([string]::IsNullOrWhiteSpace($liveCmd) -or [string]::IsNullOrWhiteSpace($liveExe)) {
        return $false
    }
    if ([string]::IsNullOrWhiteSpace($metaCmd) -or [string]::IsNullOrWhiteSpace($metaExe)) {
        return $false
    }
    if ($liveCmd -ne $metaCmd) { return $false }
    if ($liveExe -ne $metaExe) { return $false }

    $validKinds = @('backend', 'frontend', 'wrapper-backend', 'wrapper-frontend')
    if ($validKinds -notcontains [string]$Record.Kind) { return $false }
    return $true
}

function Stop-OwnedSessionProcesses {
    # Stop ONLY processes recorded for this session, after full metadata re-validation.
    # No parent/child inference at stop time.
    $records = @($script:Owned)
    foreach ($rec in $records) {
        $snap = Get-ProcessSnapshot -ProcessId ([int]$rec.Pid)
        if (-not $snap) { continue }
        if (-not (Test-SnapMatchesOwnedRecord -Snap $snap -Record $rec)) {
            Write-Warning ("Skipping PID {0}: identity no longer matches owned {1} metadata (left intact)." -f $rec.Pid, $rec.Kind)
            continue
        }
        try {
            Stop-Process -Id $snap.Pid -Force -ErrorAction SilentlyContinue
            Write-Host ("Stopped owned PID {0} ({1})" -f $snap.Pid, $rec.Kind)
        } catch {
            Write-Warning "Could not stop owned PID $($rec.Pid): $_"
        }
    }
    Remove-Item -Force (Join-Path $PidDir '*.json') -ErrorAction SilentlyContinue
    Remove-Item -Force (Join-Path $PidDir '*.pid') -ErrorAction SilentlyContinue
}

function Show-LogTail {
    param(
        [string]$LogPath,
        [int]$Lines = 40
    )
    if (-not (Test-Path $LogPath)) {
        Write-Host "No log at $LogPath"
        return
    }
    Write-Host "----- tail $LogPath -----"
    Get-Content -Path $LogPath -Tail $Lines -ErrorAction SilentlyContinue | ForEach-Object { Write-Host $_ }
    Write-Host '----- end log -----'
}

function Find-OwnedWorkerUnderWrapper {
    param(
        [int]$WrapperPid,
        [ValidateSet('backend', 'frontend')]
        [string]$Kind
    )
    if ($WrapperPid -le 0) { return $null }
    $queue = New-Object 'System.Collections.Generic.Queue[int]'
    $queue.Enqueue($WrapperPid)
    $seen = @{}
    while ($queue.Count -gt 0) {
        $parent = $queue.Dequeue()
        if ($seen.ContainsKey($parent)) { continue }
        $seen[$parent] = $true
        $children = Get-CimInstance Win32_Process -Filter "ParentProcessId=$parent" -ErrorAction SilentlyContinue
        foreach ($c in $children) {
            $cid = [int]$c.ProcessId
            $queue.Enqueue($cid)
            $snap = Get-ProcessSnapshot -ProcessId $cid
            if ($snap -and (Test-IsDiscoverableDemoWorker -Snap $snap -Kind $Kind -ExpectedParentPid $parent)) {
                return $snap
            }
        }
    }
    return $null
}

function Wait-OwnedHttpWorker {
    param(
        [string]$Url,
        [int]$Port,
        [int]$TimeoutSec,
        [ValidateSet('backend', 'frontend')]
        [string]$Kind,
        [int]$WrapperPid
    )
    $deadline = (Get-Date).AddSeconds($TimeoutSec)
    while ((Get-Date) -lt $deadline) {
        $worker = Find-OwnedWorkerUnderWrapper -WrapperPid $WrapperPid -Kind $Kind
        if ($worker -and (Test-HttpStatus200 $Url)) {
            return $worker
        }

        $listenerPid = Get-PortListenerPid -Port $Port
        if ($listenerPid -and -not $worker) {
            $listenerSnap = Get-ProcessSnapshot -ProcessId $listenerPid
            if ($listenerSnap -and (Test-IsDiscoverableDemoWorker -Snap $listenerSnap -Kind $Kind -ExpectedParentPid $WrapperPid)) {
                if (Test-HttpStatus200 $Url) {
                    return $listenerSnap
                }
            }
            if ($listenerSnap -and -not (Test-IsDiscoverableDemoWorker -Snap $listenerSnap -Kind $Kind) -and -not (Test-HttpStatus200 $Url)) {
                $wrap = Get-Process -Id $WrapperPid -ErrorAction SilentlyContinue
                if (-not $wrap) {
                    Write-Host "ERROR: Port $Port held by foreign PID $listenerPid and wrapper exited."
                    return $null
                }
            }
        }
        Start-Sleep -Milliseconds 500
    }
    return $null
}

$BackendLog = Join-Path $PidDir 'backend.log'
$FrontendLog = Join-Path $PidDir 'frontend.log'
$BackendMeta = Join-Path $PidDir 'backend.json'
$FrontendMeta = Join-Path $PidDir 'frontend.json'
$BackendWrapperMeta = Join-Path $PidDir 'backend.wrapper.json'
$FrontendWrapperMeta = Join-Path $PidDir 'frontend.wrapper.json'
$backendBat = Join-Path $PidDir 'backend_launch.cmd'
$frontendBat = Join-Path $PidDir 'frontend_launch.cmd'

try {
    $backendLines = @(
        '@echo off'
        'set EMAIL_PROVIDER=console'
        'set SKIP_SYSTEM_BOOT=1'
        'set JOBS_ENABLED=false'
        'set RUN_ETL_ON_BOOT=never'
        ('cd /d "' + $BackendDir + '"')
        ('"' + $VenvPython + '" -m uvicorn app.main:app --host 127.0.0.1 --port 8000 > "' + $BackendLog + '" 2>&1')
    )
    $backendLines | Set-Content -Path $backendBat -Encoding ASCII

    $cmdProc = Start-Process -FilePath 'cmd.exe' -ArgumentList @('/c', $backendBat) -WorkingDirectory $BackendDir -PassThru -WindowStyle Hidden
    Start-Sleep -Milliseconds 200
    $wrapperSnap = Get-ProcessSnapshot -ProcessId ([int]$cmdProc.Id)
    if (-not $wrapperSnap) {
        throw 'Backend wrapper process disappeared immediately after start.'
    }
    if (-not (Test-IsOwnedWrapper -Snap $wrapperSnap -Kind 'wrapper-backend')) {
        throw 'Backend wrapper identity could not be verified.'
    }
    Save-OwnedMeta -Snap $wrapperSnap -Kind 'wrapper-backend' -MetaPath $BackendWrapperMeta

    $backendSnap = Wait-OwnedHttpWorker -Url 'http://127.0.0.1:8000/health' -Port 8000 -TimeoutSec 60 -Kind 'backend' -WrapperPid ([int]$cmdProc.Id)
    if (-not $backendSnap -or -not (Test-HttpStatus200 'http://127.0.0.1:8000/health')) {
        Write-Host 'ERROR: Backend did not return HTTP 200 on /health within 60s.'
        Show-LogTail -LogPath $BackendLog
        Stop-OwnedSessionProcesses
        exit 1
    }
    Save-OwnedMeta -Snap $backendSnap -Kind 'backend' -MetaPath $BackendMeta

    $npmCmd = Get-Command npm.cmd -ErrorAction SilentlyContinue
    if (-not $npmCmd) {
        $npmCmd = Get-Command npm -ErrorAction SilentlyContinue
    }
    if (-not $npmCmd) {
        Write-Host 'ERROR: npm was not found on PATH.'
        Stop-OwnedSessionProcesses
        exit 1
    }

    $frontendLines = @(
        '@echo off'
        ('cd /d "' + $FrontendDir + '"')
        ('call "' + $npmCmd.Source + '" start -- --host 127.0.0.1 --port 4200 > "' + $FrontendLog + '" 2>&1')
    )
    $frontendLines | Set-Content -Path $frontendBat -Encoding ASCII

    $feCmdProc = Start-Process -FilePath 'cmd.exe' -ArgumentList @('/c', $frontendBat) -WorkingDirectory $FrontendDir -PassThru -WindowStyle Hidden
    Start-Sleep -Milliseconds 200
    $feWrapperSnap = Get-ProcessSnapshot -ProcessId ([int]$feCmdProc.Id)
    if (-not $feWrapperSnap) {
        throw 'Frontend wrapper process disappeared immediately after start.'
    }
    if (-not (Test-IsOwnedWrapper -Snap $feWrapperSnap -Kind 'wrapper-frontend')) {
        throw 'Frontend wrapper identity could not be verified.'
    }
    Save-OwnedMeta -Snap $feWrapperSnap -Kind 'wrapper-frontend' -MetaPath $FrontendWrapperMeta

    $frontendSnap = Wait-OwnedHttpWorker -Url 'http://127.0.0.1:4200/' -Port 4200 -TimeoutSec 120 -Kind 'frontend' -WrapperPid ([int]$feCmdProc.Id)
    if (-not $frontendSnap -or -not (Test-HttpStatus200 'http://127.0.0.1:4200/')) {
        Write-Host 'ERROR: Frontend did not return HTTP 200 on http://127.0.0.1:4200/ within 120s.'
        Show-LogTail -LogPath $FrontendLog
        Stop-OwnedSessionProcesses
        exit 1
    }
    Save-OwnedMeta -Snap $frontendSnap -Kind 'frontend' -MetaPath $FrontendMeta

    if (-not (Test-HttpStatus200 'http://127.0.0.1:8000/health')) {
        Write-Host 'ERROR: Backend /health is not HTTP 200 after frontend start.'
        Show-LogTail -LogPath $BackendLog
        Stop-OwnedSessionProcesses
        exit 1
    }
    if (-not (Test-HttpStatus200 'http://127.0.0.1:4200/')) {
        Write-Host 'ERROR: Frontend / is not HTTP 200 after startup.'
        Show-LogTail -LogPath $FrontendLog
        Stop-OwnedSessionProcesses
        exit 1
    }

    Write-Host 'http://127.0.0.1:4200'
    Write-Host 'http://127.0.0.1:8000/health'
    exit 0
} catch {
    Write-Host ("ERROR: start_demo failed: {0}" -f $_.Exception.Message)
    Show-LogTail -LogPath $BackendLog
    Show-LogTail -LogPath $FrontendLog
    Stop-OwnedSessionProcesses
    exit 1
}
