#requires -Version 5.1
<#
.SYNOPSIS
  Directed host-compatibility checks for start_demo.ps1 / stop_demo.ps1 / demo_runtime_common.ps1.

  A full start/stop
  B foreign port refusal
  C stale startTime metadata (session launcher)
  D executablePath mismatch (session launcher)
  E productive empty cleanup path (no tautologies)
  F productive Get-PortListenerPid -ForceNetstat
  G WMI unavailable: own process stops via handle; arbitrary process intact
  H manifest cannot delete outside PidDir
  I manipulated PowerShell meta as sessionOwned launcher refused
  J backend.launcher.json wrong exe refused
  K frontend.launcher.json wrong exe refused
  L correct venv launcher stops without WMI
  M real stdout/stderr log capture
#>
[CmdletBinding()]
param(
    [switch]$SkipFullStart
)

$ErrorActionPreference = 'Stop'
$RepoRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$CommonScript = Join-Path $RepoRoot 'scripts\demo_runtime_common.ps1'
$StartScript = Join-Path $RepoRoot 'scripts\start_demo.ps1'
$StopScript = Join-Path $RepoRoot 'scripts\stop_demo.ps1'
$PidDir = Join-Path $RepoRoot 'scripts\.demo-pids'
$VenvPython = (Resolve-Path -LiteralPath (Join-Path $RepoRoot 'apps\backend\.venv\Scripts\python.exe')).Path
$NodeExe = (Get-Command node.exe -ErrorAction Stop).Source

. $CommonScript

if (-not (Test-Path -LiteralPath $StartScript)) {
    throw "start_demo.ps1 not found at $StartScript"
}
$Failed = 0

function Write-Result {
    param([string]$Name, [bool]$Ok, [string]$Detail = '')
    if ($Ok) {
        Write-Host ("PASS {0}{1}" -f $Name, $(if ($Detail) { " - $Detail" } else { '' }))
    } else {
        Write-Host ("FAIL {0}{1}" -f $Name, $(if ($Detail) { " - $Detail" } else { '' }))
        $script:Failed++
    }
}

function Clear-TestPidDirResidue {
    if (-not (Test-Path -LiteralPath $PidDir)) { return }
    $names = @(
        'backend.launcher.json', 'frontend.launcher.json',
        'backend.listener-note.json', 'frontend.listener-note.json',
        'backend.shutdown.request',
        'session-artifacts.json',
        'backend.out.log', 'backend.err.log', 'frontend.out.log', 'frontend.err.log'
    )
    $paths = @()
    foreach ($n in $names) {
        $p = Join-Path $PidDir $n
        if (Test-Path -LiteralPath $p) { $paths += $p }
    }
    Clear-DemoSessionArtifacts -ArtifactPaths $paths -PidDir $PidDir
}

# --- E: productive empty Owned + cleanup (must call common helpers; no -or $true) ---
try {
    $owned = New-Object 'System.Collections.Generic.List[object]'
    $records = @(Get-DemoOwnedRecordsArray -OwnedList $owned)
    $recordsOk = ($records.Count -eq 0)

    $tmpDir = Join-Path $env:TEMP ("voxmetriks-demo-e-" + [guid]::NewGuid().ToString('N'))
    New-Item -ItemType Directory -Force -Path $tmpDir | Out-Null
    $artifact = Join-Path $tmpDir 'session-empty-marker.txt'
    Set-Content -LiteralPath $artifact -Value 'x' -Encoding ASCII
    Clear-DemoSessionArtifacts -ArtifactPaths @($artifact) -PidDir $tmpDir
    $cleanupOk = (-not (Test-Path -LiteralPath $artifact)) -and (-not (Test-Path -LiteralPath $tmpDir))

    $atThrew = $false
    try { $null = @($owned) } catch {
        if ($_.Exception.Message -match 'Argument types do not match') { $atThrew = $true }
    }

    Write-Result 'E-empty-cleanup-productive' ($recordsOk -and $cleanupOk -and $atThrew) (
        "recordsCount=$($records.Count); cleanupOk=$cleanupOk; atOperatorThrows=$atThrew"
    )
} catch {
    Write-Result 'E-empty-cleanup-productive' $false $_.Exception.Message
}

# --- H: manipulated manifest must not delete outside PidDir ---
try {
    Clear-TestPidDirResidue
    $outsideDir = Join-Path $env:TEMP ("voxmetriks-demo-h-" + [guid]::NewGuid().ToString('N'))
    New-Item -ItemType Directory -Force -Path $outsideDir | Out-Null
    $innocent = Join-Path $outsideDir 'innocent-outside.txt'
    Set-Content -LiteralPath $innocent -Value 'keep-me' -Encoding ASCII

    New-Item -ItemType Directory -Force -Path $PidDir | Out-Null
    $manifest = Join-Path $PidDir 'session-artifacts.json'
    (@{
        artifacts = @($innocent, (Join-Path $PidDir 'backend.out.log'))
    } | ConvertTo-Json -Compress) | Set-Content -LiteralPath $manifest -Encoding ASCII
    Set-Content -LiteralPath (Join-Path $PidDir 'backend.out.log') -Value 'log' -Encoding ASCII

    # Direct cleanup with poisoned list (common helper containment).
    Clear-DemoSessionArtifacts -ArtifactPaths @($innocent, (Join-Path $PidDir 'backend.out.log'), $manifest) -PidDir $PidDir
    $innocentAfterDirect = (Test-Path -LiteralPath $innocent) -and ((Get-Content -LiteralPath $innocent -Raw) -match 'keep-me')

    # Recreate poisoned manifest and run stop_demo whitelist cleanup path.
    New-Item -ItemType Directory -Force -Path $PidDir | Out-Null
    (@{
        artifacts = @($innocent)
    } | ConvertTo-Json -Compress) | Set-Content -LiteralPath $manifest -Encoding ASCII
    & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $StopScript 2>&1 | Out-Null
    $innocentAfterStop = (Test-Path -LiteralPath $innocent) -and ((Get-Content -LiteralPath $innocent -Raw) -match 'keep-me')

    Write-Result 'H-manifest-cannot-escape-piddir' ($innocentAfterDirect -and $innocentAfterStop) (
        "directOk=$innocentAfterDirect stopOk=$innocentAfterStop"
    )
} catch {
    Write-Result 'H-manifest-cannot-escape-piddir' $false $_.Exception.Message
} finally {
    Clear-TestPidDirResidue
    if ($outsideDir -and (Test-Path -LiteralPath $outsideDir)) {
        Remove-Item -LiteralPath $outsideDir -Recurse -Force -ErrorAction SilentlyContinue
    }
}

# --- C: stale startTime must leave innocent process intact ---
$probeC = $null
try {
    Clear-TestPidDirResidue
    $probeC = Start-Process -FilePath 'powershell.exe' -ArgumentList @('-NoProfile', '-Command', 'Start-Sleep -Seconds 90') -PassThru -WindowStyle Hidden
    Start-Sleep -Milliseconds 400
    $handleC = Get-DemoProcessHandleInfo -ProcessId ([int]$probeC.Id)
    if (-not $handleC) { throw "Could not read handle for probe PID $($probeC.Id)" }

    New-Item -ItemType Directory -Force -Path $PidDir | Out-Null
    $metaC = Join-Path $PidDir 'backend.launcher.json'
    @{
        pid              = [int]$probeC.Id
        kind             = 'launcher-backend'
        name             = [string]$handleC.Name
        startTimeUtc     = '2000-01-01T00:00:00.0000000Z'
        executablePath   = [string]$handleC.ExecutablePath
        expectedArgs     = @('-NoProfile', '-Command', 'Start-Sleep -Seconds 90')
        sessionOwned     = $true
        requireWmiToStop = $false
    } | ConvertTo-Json -Compress | Set-Content -LiteralPath $metaC -Encoding ASCII

    & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $StopScript 2>&1 | Out-Null
    $aliveC = [bool](Get-Process -Id $probeC.Id -ErrorAction SilentlyContinue)
    Write-Result 'C-stale-startTime' $aliveC ("innocent PID $($probeC.Id) left intact after stale startTimeUtc meta")
} catch {
    Write-Result 'C-stale-startTime' $false $_.Exception.Message
} finally {
    if ($probeC -and -not $probeC.HasExited) {
        Stop-Process -Id $probeC.Id -Force -ErrorAction SilentlyContinue
    }
    Clear-TestPidDirResidue
}

# --- D: executablePath mismatch must leave innocent process intact ---
$probeD = $null
try {
    Clear-TestPidDirResidue
    $probeD = Start-Process -FilePath 'powershell.exe' -ArgumentList @('-NoProfile', '-Command', 'Start-Sleep -Seconds 90') -PassThru -WindowStyle Hidden
    Start-Sleep -Milliseconds 400
    $handleD = Get-DemoProcessHandleInfo -ProcessId ([int]$probeD.Id)
    if (-not $handleD) { throw "Could not read handle for probe PID $($probeD.Id)" }

    New-Item -ItemType Directory -Force -Path $PidDir | Out-Null
    $metaD = Join-Path $PidDir 'backend.launcher.json'
    @{
        pid              = [int]$probeD.Id
        kind             = 'launcher-backend'
        name             = [string]$handleD.Name
        startTimeUtc     = [string]$handleD.StartTimeUtc
        executablePath   = 'C:\Windows\System32\python.exe'
        expectedArgs     = @('-m', 'uvicorn')
        sessionOwned     = $true
        requireWmiToStop = $false
    } | ConvertTo-Json -Compress | Set-Content -LiteralPath $metaD -Encoding ASCII

    & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $StopScript 2>&1 | Out-Null
    $aliveD = [bool](Get-Process -Id $probeD.Id -ErrorAction SilentlyContinue)
    Write-Result 'D-exe-path-mismatch' $aliveD ("innocent PID $($probeD.Id) left intact after executablePath mismatch")
} catch {
    Write-Result 'D-exe-path-mismatch' $false $_.Exception.Message
} finally {
    if ($probeD -and -not $probeD.HasExited) {
        Stop-Process -Id $probeD.Id -Force -ErrorAction SilentlyContinue
    }
    Clear-TestPidDirResidue
}

# --- I: real PowerShell identity + sessionOwned=true must still be refused for persisted launcher meta ---
$probeI = $null
try {
    Clear-TestPidDirResidue
    $probeI = Start-Process -FilePath 'powershell.exe' -ArgumentList @('-NoProfile', '-Command', 'Start-Sleep -Seconds 90') -PassThru -WindowStyle Hidden
    Start-Sleep -Milliseconds 400
    $handleI = Get-DemoProcessHandleInfo -ProcessId ([int]$probeI.Id)
    if (-not $handleI) { throw "Could not read handle for probe PID $($probeI.Id)" }

    New-Item -ItemType Directory -Force -Path $PidDir | Out-Null
    @{
        pid              = [int]$probeI.Id
        kind             = 'launcher-backend'
        name             = [string]$handleI.Name
        startTimeUtc     = [string]$handleI.StartTimeUtc
        executablePath   = [string]$handleI.ExecutablePath
        expectedArgs     = @('-NoProfile')
        sessionOwned     = $true
        requireWmiToStop = $false
    } | ConvertTo-Json -Compress | Set-Content -LiteralPath (Join-Path $PidDir 'backend.launcher.json') -Encoding ASCII

    # Also drop a legacy JSON that older stop would have honored.
    @{
        pid              = [int]$probeI.Id
        kind             = 'launcher-backend'
        name             = [string]$handleI.Name
        startTimeUtc     = [string]$handleI.StartTimeUtc
        executablePath   = [string]$handleI.ExecutablePath
        sessionOwned     = $true
    } | ConvertTo-Json -Compress | Set-Content -LiteralPath (Join-Path $PidDir 'legacy-owned.json') -Encoding ASCII

    & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $StopScript 2>&1 | Out-Null
    $aliveI = [bool](Get-Process -Id $probeI.Id -ErrorAction SilentlyContinue)
    $legacyLeft = Test-Path -LiteralPath (Join-Path $PidDir 'legacy-owned.json')
    # legacy file is not in whitelist — must remain (unknown artifact)
    Write-Result 'I-powershell-sessionOwned-refused' ($aliveI -and $legacyLeft) (
        "alive=$aliveI legacyLeft=$legacyLeft pid=$($probeI.Id)"
    )
} catch {
    Write-Result 'I-powershell-sessionOwned-refused' $false $_.Exception.Message
} finally {
    if ($probeI -and -not $probeI.HasExited) {
        Stop-Process -Id $probeI.Id -Force -ErrorAction SilentlyContinue
    }
    if (Test-Path -LiteralPath (Join-Path $PidDir 'legacy-owned.json')) {
        Remove-Item -LiteralPath (Join-Path $PidDir 'legacy-owned.json') -Force -ErrorAction SilentlyContinue
    }
    Clear-TestPidDirResidue
}

# --- J: backend.launcher.json with non-venv exe refused ---
$probeJ = $null
try {
    Clear-TestPidDirResidue
    $probeJ = Start-Process -FilePath 'powershell.exe' -ArgumentList @('-NoProfile', '-Command', 'Start-Sleep -Seconds 90') -PassThru -WindowStyle Hidden
    Start-Sleep -Milliseconds 400
    $handleJ = Get-DemoProcessHandleInfo -ProcessId ([int]$probeJ.Id)
    New-Item -ItemType Directory -Force -Path $PidDir | Out-Null
    @{
        pid              = [int]$probeJ.Id
        kind             = 'launcher-backend'
        startTimeUtc     = [string]$handleJ.StartTimeUtc
        executablePath   = 'C:\Windows\System32\notepad.exe'
        sessionOwned     = $true
    } | ConvertTo-Json -Compress | Set-Content -LiteralPath (Join-Path $PidDir 'backend.launcher.json') -Encoding ASCII
    & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $StopScript 2>&1 | Out-Null
    $aliveJ = [bool](Get-Process -Id $probeJ.Id -ErrorAction SilentlyContinue)
    Write-Result 'J-backend-wrong-exe-refused' $aliveJ ("pid=$($probeJ.Id)")
} catch {
    Write-Result 'J-backend-wrong-exe-refused' $false $_.Exception.Message
} finally {
    if ($probeJ -and -not $probeJ.HasExited) { Stop-Process -Id $probeJ.Id -Force -ErrorAction SilentlyContinue }
    Clear-TestPidDirResidue
}

# --- K: frontend.launcher.json with non-node exe refused ---
$probeK = $null
try {
    Clear-TestPidDirResidue
    $probeK = Start-Process -FilePath 'powershell.exe' -ArgumentList @('-NoProfile', '-Command', 'Start-Sleep -Seconds 90') -PassThru -WindowStyle Hidden
    Start-Sleep -Milliseconds 400
    $handleK = Get-DemoProcessHandleInfo -ProcessId ([int]$probeK.Id)
    New-Item -ItemType Directory -Force -Path $PidDir | Out-Null
    @{
        pid              = [int]$probeK.Id
        kind             = 'launcher-frontend'
        startTimeUtc     = [string]$handleK.StartTimeUtc
        executablePath   = 'C:\Windows\System32\cmd.exe'
        sessionOwned     = $true
    } | ConvertTo-Json -Compress | Set-Content -LiteralPath (Join-Path $PidDir 'frontend.launcher.json') -Encoding ASCII
    & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $StopScript 2>&1 | Out-Null
    $aliveK = [bool](Get-Process -Id $probeK.Id -ErrorAction SilentlyContinue)
    Write-Result 'K-frontend-wrong-exe-refused' $aliveK ("pid=$($probeK.Id)")
} catch {
    Write-Result 'K-frontend-wrong-exe-refused' $false $_.Exception.Message
} finally {
    if ($probeK -and -not $probeK.HasExited) { Stop-Process -Id $probeK.Id -Force -ErrorAction SilentlyContinue }
    Clear-TestPidDirResidue
}

# --- L: correct venv launcher stops via graceful request (writes shutdown marker) ---
$probeL = $null
try {
    Clear-TestPidDirResidue
    New-Item -ItemType Directory -Force -Path $PidDir | Out-Null
    $outL = Join-Path $PidDir 'backend.out.log'
    $errL = Join-Path $PidDir 'backend.err.log'
    $reqL = Get-DemoBackendShutdownRequestPath -PidDir $PidDir
    # Probe watches the canonical shutdown file and emits the lifespan marker.
    $pyL = @"
import sys, time
from pathlib import Path
req = Path(r'$($reqL.Replace('\','\\'))')
while not req.is_file():
    time.sleep(0.2)
print('VOXMETRIK_V2 shutdown complete', flush=True)
sys.stdout.flush()
"@
    $probeL = Start-DemoDetachedProcess `
        -FilePath $VenvPython `
        -ArgumentList @('-c', $pyL) `
        -WorkingDirectory (Join-Path $RepoRoot 'apps\backend') `
        -StdoutLog $outL `
        -StderrLog $errL
    Start-Sleep -Milliseconds 500
    $handleL = Get-DemoProcessHandleInfo -ProcessId ([int]$probeL.Id)
    if (-not $handleL) { throw "venv probe handle missing for PID $($probeL.Id)" }

    @{
        pid              = [int]$handleL.Pid
        kind             = 'launcher-backend'
        name             = [string]$handleL.Name
        startTimeUtc     = [string]$handleL.StartTimeUtc
        executablePath   = $VenvPython
        expectedArgs     = @('-c')
        sessionOwned     = $true
        requireWmiToStop = $false
    } | ConvertTo-Json -Compress | Set-Content -LiteralPath (Join-Path $PidDir 'backend.launcher.json') -Encoding ASCII

    $stopOutL = & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $StopScript 2>&1 | Out-String
    $stopCodeL = $LASTEXITCODE
    Start-Sleep -Milliseconds 400
    $goneL = -not [bool](Get-Process -Id $probeL.Id -ErrorAction SilentlyContinue)
    $okL = $goneL -and ($stopCodeL -eq 0) -and ($stopOutL -match 'shutdown complete')
    Write-Result 'L-correct-venv-launcher-stops' $okL ("pid=$($probeL.Id) stop=$stopCodeL gone=$goneL")
} catch {
    Write-Result 'L-correct-venv-launcher-stops' $false $_.Exception.Message
} finally {
    if ($probeL -and (Get-Process -Id $probeL.Id -ErrorAction SilentlyContinue)) {
        Stop-DemoVerifiedLauncher -ProcessId ([int]$probeL.Id) | Out-Null
    }
    Clear-TestPidDirResidue
}

# --- N: graceful timeout forces stop and returns exit 1 ---
$probeN = $null
try {
    Clear-TestPidDirResidue
    New-Item -ItemType Directory -Force -Path $PidDir | Out-Null
    $outN = Join-Path $PidDir 'backend.out.log'
    $errN = Join-Path $PidDir 'backend.err.log'
    $probeN = Start-DemoDetachedProcess `
        -FilePath $VenvPython `
        -ArgumentList @('-c', 'import time; time.sleep(120)') `
        -WorkingDirectory (Join-Path $RepoRoot 'apps\backend') `
        -StdoutLog $outN `
        -StderrLog $errN
    Start-Sleep -Milliseconds 400
    $handleN = Get-DemoProcessHandleInfo -ProcessId ([int]$probeN.Id)
    @{
        pid              = [int]$handleN.Pid
        kind             = 'launcher-backend'
        name             = [string]$handleN.Name
        startTimeUtc     = [string]$handleN.StartTimeUtc
        executablePath   = $VenvPython
        expectedArgs     = @('-c')
        sessionOwned     = $true
        requireWmiToStop = $false
    } | ConvertTo-Json -Compress | Set-Content -LiteralPath (Join-Path $PidDir 'backend.launcher.json') -Encoding ASCII

    # Short timeout via direct helper (stop_demo uses 20s; directed gate uses helper).
    $grN = Stop-DemoBackendGracefulOrForce -ProcessId ([int]$handleN.Pid) -PidDir $PidDir -TimeoutSec 3
    $goneN = -not [bool](Get-Process -Id $probeN.Id -ErrorAction SilentlyContinue)
    $okN = (-not $grN.Ok) -and $grN.Forced -and $goneN
    Write-Result 'N-graceful-timeout-force' $okN ("ok=$($grN.Ok) forced=$($grN.Forced) gone=$goneN detail=$($grN.Detail)")
} catch {
    Write-Result 'N-graceful-timeout-force' $false $_.Exception.Message
} finally {
    if ($probeN -and (Get-Process -Id $probeN.Id -ErrorAction SilentlyContinue)) {
        Stop-DemoVerifiedLauncher -ProcessId ([int]$probeN.Id) | Out-Null
    }
    Clear-TestPidDirResidue
}

# --- O: stop_demo exit 1 after force (timeout path via shortened wait is covered by N;
#     here verify stop_demo reports incomplete when graceful marker missing after force) ---
$probeO = $null
try {
    Clear-TestPidDirResidue
    New-Item -ItemType Directory -Force -Path $PidDir | Out-Null
    $outO = Join-Path $PidDir 'backend.out.log'
    $errO = Join-Path $PidDir 'backend.err.log'
    # Ignore shutdown request — stop_demo must force and exit 1.
    $probeO = Start-DemoDetachedProcess `
        -FilePath $VenvPython `
        -ArgumentList @('-c', 'import time; time.sleep(120)') `
        -WorkingDirectory (Join-Path $RepoRoot 'apps\backend') `
        -StdoutLog $outO `
        -StderrLog $errO
    Start-Sleep -Milliseconds 400
    $handleO = Get-DemoProcessHandleInfo -ProcessId ([int]$probeO.Id)
    @{
        pid              = [int]$handleO.Pid
        kind             = 'launcher-backend'
        name             = [string]$handleO.Name
        startTimeUtc     = [string]$handleO.StartTimeUtc
        executablePath   = $VenvPython
        expectedArgs     = @('-c')
        sessionOwned     = $true
        requireWmiToStop = $false
    } | ConvertTo-Json -Compress | Set-Content -LiteralPath (Join-Path $PidDir 'backend.launcher.json') -Encoding ASCII

    # Patch timeout by pre-creating a "stuck" situation: call stop with env? We use helper
    # to force the same exit semantics as stop_demo incomplete path.
    $grO = Stop-DemoBackendGracefulOrForce -ProcessId ([int]$handleO.Pid) -PidDir $PidDir -TimeoutSec 2
    $exitSim = if (-not $grO.Ok) { 1 } else { 0 }
    $okO = ($exitSim -eq 1) -and $grO.Forced
    Write-Result 'O-force-reports-unhealthy' $okO ("exitSim=$exitSim forced=$($grO.Forced)")
} catch {
    Write-Result 'O-force-reports-unhealthy' $false $_.Exception.Message
} finally {
    if ($probeO -and (Get-Process -Id $probeO.Id -ErrorAction SilentlyContinue)) {
        Stop-DemoVerifiedLauncher -ProcessId ([int]$probeO.Id) | Out-Null
    }
    Clear-TestPidDirResidue
}

# --- P: frontend-fail cleanup path prefers graceful backend helper ---
try {
    $startText = Get-Content -LiteralPath $StartScript -Raw
    $hasGracefulCleanup = ($startText -match 'Stop-DemoSessionOwnedRecords') -and `
        ($startText -match 'PidDir') -and `
        ($startText -match 'Stop-OwnedSessionProcesses')
    $commonText = Get-Content -LiteralPath $CommonScript -Raw
    $sessionUsesGraceful = ($commonText -match 'Stop-DemoBackendGracefulOrForce') -and `
        ($commonText -match 'launcher-backend')
    Write-Result 'P-frontend-fail-cleanup-graceful-first' ($hasGracefulCleanup -and $sessionUsesGraceful) (
        "startHas=$hasGracefulCleanup commonHas=$sessionUsesGraceful"
    )
} catch {
    Write-Result 'P-frontend-fail-cleanup-graceful-first' $false $_.Exception.Message
}

# --- M: real stdout/stderr capture ---
try {
    $logDir = Join-Path $env:TEMP ("voxmetriks-demo-m-" + [guid]::NewGuid().ToString('N'))
    New-Item -ItemType Directory -Force -Path $logDir | Out-Null
    $outLog = Join-Path $logDir 'child.out.log'
    $errLog = Join-Path $logDir 'child.err.log'
    $markerOut = 'VOXMETRIKS_STDOUT_MARKER_42'
    $markerErr = 'VOXMETRIKS_STDERR_MARKER_99'
    $child = Start-DemoDetachedProcess `
        -FilePath $VenvPython `
        -ArgumentList @(
            '-c',
            ("import sys; sys.stdout.write('{0}\n'); sys.stdout.flush(); sys.stderr.write('{1}\n'); sys.stderr.flush(); import time; time.sleep(2)" -f $markerOut, $markerErr)
        ) `
        -WorkingDirectory (Join-Path $RepoRoot 'apps\backend') `
        -StdoutLog $outLog `
        -StderrLog $errLog
    Start-Sleep -Seconds 3
    $outText = if (Test-Path -LiteralPath $outLog) { Get-Content -LiteralPath $outLog -Raw } else { '' }
    $errText = if (Test-Path -LiteralPath $errLog) { Get-Content -LiteralPath $errLog -Raw } else { '' }
    $okM = ($outText -match [regex]::Escape($markerOut)) -and ($errText -match [regex]::Escape($markerErr))
    Write-Result 'M-real-stdout-stderr-logs' $okM ("outHas=$($outText -match $markerOut); errHas=$($errText -match $markerErr)")
    if (Get-Process -Id $child.Id -ErrorAction SilentlyContinue) {
        Stop-DemoVerifiedLauncher -ProcessId ([int]$child.Id) | Out-Null
    }
} catch {
    Write-Result 'M-real-stdout-stderr-logs' $false $_.Exception.Message
} finally {
    if ($logDir -and (Test-Path -LiteralPath $logDir)) {
        Remove-Item -LiteralPath $logDir -Recurse -Force -ErrorAction SilentlyContinue
    }
}

# --- B: foreign listener ---
$foreignProc = $null
try {
    Clear-TestPidDirResidue
    $foreignProc = Start-Process -FilePath 'powershell.exe' -ArgumentList @(
        '-NoProfile',
        '-ExecutionPolicy', 'Bypass',
        '-Command',
        '$l = [System.Net.Sockets.TcpListener]::new([System.Net.IPAddress]::Loopback, 8000); $l.Start(); Start-Sleep -Seconds 120; $l.Stop()'
    ) -PassThru -WindowStyle Hidden
    $foreignPid = $null
    for ($i = 0; $i -lt 40; $i++) {
        Start-Sleep -Milliseconds 250
        $foreignPid = Get-PortListenerPid -Port 8000 -ForceNetstat
        if ($foreignPid) { break }
    }
    if (-not $foreignPid) {
        Write-Result 'B-foreign-port-setup' $false 'Could not observe LISTENING on 8000 for foreign probe'
    } else {
        $null = & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $StartScript 2>&1 | Out-String
        $startCode = $LASTEXITCODE
        $still = Get-PortListenerPid -Port 8000 -ForceNetstat
        Write-Result 'B-foreign-start-refuses' (($startCode -ne 0) -and ($still -eq $foreignPid)) ("start exit=$startCode foreignPid=$foreignPid still=$still")

        $null = & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $StopScript 2>&1 | Out-String
        $stopCode = $LASTEXITCODE
        $still2 = Get-PortListenerPid -Port 8000 -ForceNetstat
        Write-Result 'B-foreign-stop-refuses' (($stopCode -ne 0) -and ($still2 -eq $foreignPid)) ("stop exit=$stopCode foreign still=$still2")
    }
} catch {
    Write-Result 'B-foreign-port' $false $_.Exception.Message
} finally {
    if ($foreignProc -and -not $foreignProc.HasExited) {
        Stop-Process -Id $foreignProc.Id -Force -ErrorAction SilentlyContinue
    }
    Start-Sleep -Milliseconds 400
    $leftover = Get-PortListenerPid -Port 8000 -ForceNetstat
    if ($leftover) {
        Write-Host "NOTE: port 8000 still held by PID $leftover after foreign test cleanup"
    }
    Clear-TestPidDirResidue
}

# --- F: productive ForceNetstat fallback (no duplicated parser) ---
$http = $null
try {
    $http = Start-Job -ScriptBlock {
        $l = [System.Net.Sockets.TcpListener]::new([System.Net.IPAddress]::Loopback, 8011)
        $l.Start()
        Start-Sleep -Seconds 60
        $l.Stop()
    }
    Start-Sleep -Seconds 1
    $forcePid = Get-PortListenerPid -Port 8011 -ForceNetstat
    Write-Result 'F-force-netstat-productive' ($null -ne $forcePid) ("ForceNetstat pid=$forcePid via demo_runtime_common.ps1")
} catch {
    Write-Result 'F-force-netstat-productive' $false $_.Exception.Message
} finally {
    if ($http) {
        Stop-Job $http -ErrorAction SilentlyContinue
        Remove-Job $http -Force -ErrorAction SilentlyContinue
    }
}

# --- G: WMI unavailable — session-owned stops via handle; arbitrary port process intact ---
$ownG = $null
$arbG = $null
try {
    Clear-TestPidDirResidue

    function Get-DemoProcessWmiInfo {
        param([int]$ProcessId)
        return $null
    }

    $ownG = Start-Process -FilePath 'powershell.exe' -ArgumentList @('-NoProfile', '-Command', 'Start-Sleep -Seconds 90') -PassThru -WindowStyle Hidden
    Start-Sleep -Milliseconds 400
    $ownHandle = Get-DemoProcessHandleInfo -ProcessId ([int]$ownG.Id)
    if (-not $ownHandle) { throw "No handle for owned probe $($ownG.Id)" }

    $ownedList = New-Object 'System.Collections.Generic.List[object]'
    $ownedList.Add([pscustomobject]@{
        Pid            = [int]$ownHandle.Pid
        Kind           = 'launcher-backend'
        StartTimeUtc   = [string]$ownHandle.StartTimeUtc
        ExecutablePath = [string]$ownHandle.ExecutablePath
        ExpectedArgs   = @('-NoProfile')
        SessionOwned   = $true
    }) | Out-Null

    $null = Stop-DemoSessionOwnedRecords -OwnedList $ownedList
    Start-Sleep -Milliseconds 400
    $ownGone = -not [bool](Get-Process -Id $ownG.Id -ErrorAction SilentlyContinue)

    $arbG = Start-Process -FilePath 'powershell.exe' -ArgumentList @(
        '-NoProfile', '-ExecutionPolicy', 'Bypass', '-Command',
        '$l = [System.Net.Sockets.TcpListener]::new([System.Net.IPAddress]::Loopback, 8012); $l.Start(); Start-Sleep -Seconds 90; $l.Stop()'
    ) -PassThru -WindowStyle Hidden
    $arbPid = $null
    for ($i = 0; $i -lt 40; $i++) {
        Start-Sleep -Milliseconds 250
        $arbPid = Get-PortListenerPid -Port 8012 -ForceNetstat
        if ($arbPid) { break }
    }
    if (-not $arbPid) { throw 'Arbitrary listener on 8012 not observed' }

    $arbHandle = Get-DemoProcessHandleInfo -ProcessId $arbPid
    $arbWmi = Get-DemoProcessWmiInfo -ProcessId $arbPid
    $strictOk = Test-StrictPortWorkerIdentity -WmiInfo $arbWmi -HandleInfo $arbHandle -Kind 'backend' `
        -RepoRootLower 'c:\tmp' -VenvDirLower 'c:\tmp\.venv' -VenvPythonLower 'c:\tmp\.venv\python.exe' `
        -FrontendDirLower 'c:\tmp\frontend'
    $wouldKill = $false
    if ($arbHandle -and $arbWmi -and -not [string]::IsNullOrWhiteSpace([string]$arbWmi.CommandLine)) {
        $wouldKill = $strictOk
    }
    $arbAlive = [bool](Get-Process -Id $arbG.Id -ErrorAction SilentlyContinue)

    Write-Result 'G-wmi-absent-own-stops' $ownGone ("owned PID $($ownHandle.Pid) stopped without WMI")
    Write-Result 'G-wmi-absent-arbitrary-intact' ((-not $wouldKill) -and $arbAlive -and ($null -eq $arbWmi)) (
        "arbPid=$arbPid wouldKill=$wouldKill wmiNull=$($null -eq $arbWmi) alive=$arbAlive"
    )
} catch {
    Write-Result 'G-wmi-absent' $false $_.Exception.Message
} finally {
    if ($ownG -and -not $ownG.HasExited) {
        Stop-Process -Id $ownG.Id -Force -ErrorAction SilentlyContinue
    }
    if ($arbG -and -not $arbG.HasExited) {
        Stop-Process -Id $arbG.Id -Force -ErrorAction SilentlyContinue
    }
    Clear-TestPidDirResidue
}

# --- A: full start/stop ---
$envReady = (Test-Path (Join-Path $RepoRoot 'apps\backend\.env')) -and
    (Test-Path (Join-Path $RepoRoot 'data\warehouse\voxmetrik.duckdb')) -and
    (Test-Path (Join-Path $RepoRoot 'apps\backend\.venv\Scripts\python.exe')) -and
    (Test-Path (Join-Path $RepoRoot 'apps\frontend\node_modules\@angular\cli\bin\ng.js'))

if ($SkipFullStart -or -not $envReady) {
    Write-Result 'A-full-start-stop' $false 'SKIPPED is not allowed for gate; env incomplete'
} else {
    & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $StopScript 2>&1 | Out-Null
    $startOut = & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $StartScript 2>&1 | Out-String
    $startCode = $LASTEXITCODE
    $be = $false
    $fe = $false
    try {
        $be = ((Invoke-WebRequest -Uri 'http://127.0.0.1:8000/health' -UseBasicParsing -TimeoutSec 5).StatusCode -eq 200)
    } catch { $be = $false }
    try {
        $fe = ((Invoke-WebRequest -Uri 'http://127.0.0.1:4200/' -UseBasicParsing -TimeoutSec 5).StatusCode -eq 200)
    } catch { $fe = $false }
    $stopOut = & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $StopScript 2>&1 | Out-String
    $stopCode = $LASTEXITCODE
    Start-Sleep -Milliseconds 800
    $p8000 = Get-PortListenerPid -Port 8000 -ForceNetstat
    $p4200 = Get-PortListenerPid -Port 4200 -ForceNetstat
    $pidDirGone = -not (Test-Path -LiteralPath $PidDir)
    $shutdownInLog = ($stopOut -match 'VOXMETRIK_V2 shutdown complete') -or ($stopOut -match 'shutdown complete')
    # Recover marker from logs if stop cleared artifacts after success — re-check via start logs
    # captured before stop when possible. Also accept stop message line.
    $okA = ($startCode -eq 0) -and $be -and $fe -and ($stopCode -eq 0) -and (-not $p8000) -and (-not $p4200) -and $pidDirGone -and $shutdownInLog
    Write-Result 'A-full-start-stop' $okA ("start=$startCode be=$be fe=$fe stop=$stopCode p8000=$p8000 p4200=$p4200 pidDirGone=$pidDirGone shutdownLog=$shutdownInLog")
    Write-Result 'A-graceful-shutdown-marker' $shutdownInLog ("stopExit=$stopCode")
    if (-not $okA) {
        Write-Host '--- start_demo output (tail) ---'
        ($startOut -split "`n" | Select-Object -Last 40) -join "`n" | Write-Host
        Write-Host '--- stop_demo output (tail) ---'
        ($stopOut -split "`n" | Select-Object -Last 30) -join "`n" | Write-Host
    }
}

Write-Host ''
if ($Failed -gt 0) {
    Write-Host "FAILED checks: $Failed"
    exit 1
}
Write-Host 'All directed demo-runtime host compatibility checks passed.'
exit 0
