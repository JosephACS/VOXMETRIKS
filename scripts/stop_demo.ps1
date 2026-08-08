#requires -Version 5.1
<#
.SYNOPSIS
  Stop demo processes started by start_demo.ps1 for THIS repo only.
  Requires full metadata match (pid/start/exe/cmdline/kind) before Stop-Process.
#>
[CmdletBinding()]
param()

$ErrorActionPreference = 'Continue'
$RepoRoot = Split-Path -Parent $PSScriptRoot
$PidDir = Join-Path $RepoRoot 'scripts\.demo-pids'
$BackendDir = Join-Path $RepoRoot 'apps\backend'
$FrontendDir = Join-Path $RepoRoot 'apps\frontend'
$VenvPython = Join-Path $BackendDir '.venv\Scripts\python.exe'
$RepoRootLower = $RepoRoot.ToLowerInvariant()
$BackendDirLower = $BackendDir.ToLowerInvariant()
$FrontendDirLower = $FrontendDir.ToLowerInvariant()
$VenvDirLower = (Join-Path $BackendDir '.venv').ToLowerInvariant()
$VenvPythonLower = $VenvPython.ToLowerInvariant()
if (Test-Path -LiteralPath $VenvPython) {
    $VenvPythonLower = (Resolve-Path -LiteralPath $VenvPython).Path.ToLowerInvariant()
}
$PidDirLower = $PidDir.ToLowerInvariant()

$script:ForeignPort = $false

function Get-PortListenerPid {
    param([int]$Port)
    $conn = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue |
        Select-Object -First 1
    if ($conn -and $conn.OwningProcess) {
        return [int]$conn.OwningProcess
    }
    return $null
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

function Test-IsStrictOwnedWithoutMeta {
    <#
      Port reclaim without metadata. Safety first: missing commandLine => refuse.
      No broad "any venv python" / "any frontend node" fallbacks.
    #>
    param(
        [object]$Snap,
        [ValidateSet('backend', 'frontend', 'wrapper-backend', 'wrapper-frontend')]
        [string]$Kind
    )
    if (-not $Snap) { return $false }
    $cmd = [string]$Snap.CommandLine
    $exe = [string]$Snap.ExecutablePath
    $name = ([string]$Snap.Name).ToLowerInvariant()
    if ([string]::IsNullOrWhiteSpace($cmd)) { return $false }

    switch ($Kind) {
        'backend' {
            if ($name -notmatch '^(python|pythonw)$') { return $false }
            $exeInVenv = Test-PathMatch $exe $VenvDirLower
            if (-not $exeInVenv) { return $false }
            if ($cmd -notmatch 'uvicorn') { return $false }
            if ($cmd -notmatch 'app\.main') { return $false }
            if (-not (Test-PathMatch $cmd $RepoRootLower)) { return $false }
            return $true
        }
        'frontend' {
            if ($name -ne 'node') { return $false }
            if (-not (Test-PathMatch $cmd $FrontendDirLower)) { return $false }
            if ($cmd -notmatch 'ng serve|ng\.js|@angular[/\\]cli') { return $false }
            return $true
        }
        'wrapper-backend' {
            if ($name -ne 'cmd') { return $false }
            return (Test-PathMatch $cmd ($PidDirLower + '\backend_launch.cmd'))
        }
        'wrapper-frontend' {
            if ($name -ne 'cmd') { return $false }
            return (Test-PathMatch $cmd ($PidDirLower + '\frontend_launch.cmd'))
        }
    }
    return $false
}

function Resolve-StrictKindWithoutMeta {
    param([object]$Snap)
    foreach ($kind in @('backend', 'frontend', 'wrapper-backend', 'wrapper-frontend')) {
        if (Test-IsStrictOwnedWithoutMeta -Snap $Snap -Kind $kind) {
            return $kind
        }
    }
    return $null
}

function Test-LiveMatchesMeta {
    param(
        [object]$Snap,
        [object]$Meta
    )
    if (-not $Snap -or -not $Meta) { return $false }

    $pidVal = 0
    if (-not [int]::TryParse([string]$Meta.pid, [ref]$pidVal)) { return $false }
    if ([int]$Snap.Pid -ne $pidVal) { return $false }

    $kind = [string]$Meta.kind
    if (@('backend', 'frontend', 'wrapper-backend', 'wrapper-frontend') -notcontains $kind) {
        return $false
    }

    $expectedStart = [string]$Meta.startTimeUtc
    if ([string]::IsNullOrWhiteSpace($expectedStart)) { return $false }
    if ([string]$Snap.StartTimeUtc -ne $expectedStart) { return $false }

    $liveCmd = Normalize-IdentityText ([string]$Snap.CommandLine)
    $liveExe = Normalize-IdentityText ([string]$Snap.ExecutablePath)
    $metaCmd = Normalize-IdentityText ([string]$Meta.commandLine)
    $metaExe = Normalize-IdentityText ([string]$Meta.executablePath)

    if ([string]::IsNullOrWhiteSpace($liveCmd) -or [string]::IsNullOrWhiteSpace($liveExe)) {
        return $false
    }
    if ([string]::IsNullOrWhiteSpace($metaCmd) -or [string]::IsNullOrWhiteSpace($metaExe)) {
        return $false
    }
    if ($liveCmd -ne $metaCmd) { return $false }
    if ($liveExe -ne $metaExe) { return $false }
    return $true
}

function Stop-VerifiedProcess {
    param(
        [object]$Snap,
        [string]$Kind,
        [string]$Source
    )
    if (-not $Snap) { return }
    # Port path: strict command ownership only (no parent/child expansion).
    if (-not (Test-IsStrictOwnedWithoutMeta -Snap $Snap -Kind $Kind)) {
        Write-Warning ("Refusing to stop PID {0} from {1}: command/type does not match {2} for this repo." -f $Snap.Pid, $Source, $Kind)
        return
    }
    try {
        Stop-Process -Id $Snap.Pid -Force -ErrorAction Stop
        Write-Host ("Stopped PID {0} ({1}) from {2}" -f $Snap.Pid, $Kind, $Source)
    } catch {
        Write-Warning "Could not stop PID $($Snap.Pid): $_"
    }
}

function Read-MetaRecord {
    param([string]$Path)
    if (-not (Test-Path $Path)) { return $null }
    try {
        $raw = Get-Content -Path $Path -Raw -ErrorAction Stop
        if ([string]::IsNullOrWhiteSpace($raw)) { return $null }
        return ($raw | ConvertFrom-Json)
    } catch {
        Write-Warning "Invalid metadata at $Path"
        return $null
    }
}

function Stop-FromMetaFile {
    param([string]$Path)
    $meta = Read-MetaRecord -Path $Path
    if (-not $meta) { return }

    $pidVal = 0
    if (-not [int]::TryParse([string]$meta.pid, [ref]$pidVal)) {
        Write-Warning "Invalid pid in $Path"
        return
    }
    $kind = [string]$meta.kind
    if (@('backend', 'frontend', 'wrapper-backend', 'wrapper-frontend') -notcontains $kind) {
        Write-Warning "Unknown kind '$kind' in $Path - refusing stop."
        return
    }

    $snap = Get-ProcessSnapshot -ProcessId $pidVal
    if (-not $snap) {
        Write-Host "PID $pidVal not running - ($([IO.Path]::GetFileName($Path)))"
        return
    }

    if (-not (Test-LiveMatchesMeta -Snap $snap -Meta $meta)) {
        Write-Warning ("Refusing to stop PID {0} from {1}: metadata mismatch (pid/start/exe/cmdline/kind). Process left intact." -f $pidVal, ([IO.Path]::GetFileName($Path)))
        return
    }

    try {
        Stop-Process -Id $snap.Pid -Force -ErrorAction Stop
        Write-Host ("Stopped PID {0} ({1}) from {2}" -f $snap.Pid, $kind, ([IO.Path]::GetFileName($Path)))
    } catch {
        Write-Warning "Could not stop PID $($snap.Pid): $_"
    }
}

function Remove-DemoPidDir {
    if (-not (Test-Path $PidDir)) { return }
    for ($i = 0; $i -lt 8; $i++) {
        try {
            Get-ChildItem -LiteralPath $PidDir -Force -ErrorAction SilentlyContinue | ForEach-Object {
                Remove-Item -LiteralPath $_.FullName -Force -Recurse -ErrorAction Stop
            }
            Remove-Item -LiteralPath $PidDir -Force -Recurse -ErrorAction Stop
            if (-not (Test-Path $PidDir)) { return }
        } catch {
            Start-Sleep -Milliseconds 250
        }
    }
    if (Test-Path $PidDir) {
        Write-Warning "Could not fully remove $PidDir (file lock). Ports are free but folder remains."
    }
}

if (Test-Path $PidDir) {
    $metaFiles = @(Get-ChildItem -Path $PidDir -Filter '*.json' -ErrorAction SilentlyContinue)
    foreach ($f in $metaFiles) {
        Stop-FromMetaFile -Path $f.FullName
    }
    $legacy = @(Get-ChildItem -Path $PidDir -Filter '*.pid' -ErrorAction SilentlyContinue)
    foreach ($f in $legacy) {
        Write-Warning "Ignoring legacy PID file $($f.Name) without identity metadata (will not stop by PID alone)."
    }
} else {
    Write-Host 'No scripts/.demo-pids metadata - will still inspect ports 8000/4200 for owned listeners.'
}

foreach ($port in @(8000, 4200)) {
    $listenerPid = Get-PortListenerPid -Port $port
    if (-not $listenerPid) { continue }

    $snap = Get-ProcessSnapshot -ProcessId $listenerPid
    if (-not $snap -or [string]::IsNullOrWhiteSpace([string]$snap.CommandLine)) {
        $script:ForeignPort = $true
        Write-Warning ("Port {0} PID {1}: commandLine unavailable - refusing stop (left intact)." -f $port, $listenerPid)
        continue
    }

    $kind = Resolve-StrictKindWithoutMeta -Snap $snap
    if ($kind) {
        Stop-VerifiedProcess -Snap $snap -Kind $kind -Source "port:$port"
    } else {
        $script:ForeignPort = $true
        Write-Warning ("Port {0} is in use by PID {1} outside this repo demo stack - left running." -f $port, $listenerPid)
    }
}

Start-Sleep -Milliseconds 500

$stillBusy = @()
foreach ($port in @(8000, 4200)) {
    if (Get-PortListenerPid -Port $port) {
        $stillBusy += $port
    }
}

if ($stillBusy.Count -gt 0 -or $script:ForeignPort) {
    Write-Warning ("Ports not fully free: {0}" -f (($stillBusy -join ', ')))
    Write-Host 'stop_demo incomplete'
    exit 1
}

Remove-DemoPidDir
Write-Host 'Ports 8000 and 4200 are free.'
Write-Host 'stop_demo complete'
exit 0
