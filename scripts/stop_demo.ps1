#requires -Version 5.1
<#
.SYNOPSIS
  Stop demo processes started by start_demo.ps1 (PID files under scripts/.demo-pids).
#>
[CmdletBinding()]
param()

$ErrorActionPreference = 'Continue'
$RepoRoot = Split-Path -Parent $PSScriptRoot
$PidDir = Join-Path $RepoRoot 'scripts\.demo-pids'

$allowedNames = @('python', 'pythonw', 'node', 'npm', 'cmd')
# note: PIDs from start_demo resolve to python/node listeners when possible

if (-not (Test-Path $PidDir)) {
    Write-Host "No pid directory at scripts/.demo-pids — nothing to stop."
    exit 0
}

$pidFiles = Get-ChildItem -Path $PidDir -Filter '*.pid' -ErrorAction SilentlyContinue
if (-not $pidFiles) {
    Write-Host "No *.pid files — nothing to stop."
    exit 0
}

foreach ($f in $pidFiles) {
    $raw = (Get-Content -Path $f.FullName -ErrorAction SilentlyContinue | Select-Object -First 1)
    if (-not $raw) {
        Remove-Item -Force $f.FullName -ErrorAction SilentlyContinue
        continue
    }
    $procId = 0
    if (-not [int]::TryParse($raw.Trim(), [ref]$procId)) {
        Write-Warning "Invalid PID in $($f.Name)"
        Remove-Item -Force $f.FullName -ErrorAction SilentlyContinue
        continue
    }
    $proc = Get-Process -Id $procId -ErrorAction SilentlyContinue
    if (-not $proc) {
        Write-Host "PID $procId not running — removing $($f.Name)"
        Remove-Item -Force $f.FullName -ErrorAction SilentlyContinue
        continue
    }
    $name = $proc.ProcessName.ToLowerInvariant()
    if ($allowedNames -notcontains $name) {
        Write-Warning "Skipping PID $procId (name=$name) — not python/node/npm/cmd"
        Remove-Item -Force $f.FullName -ErrorAction SilentlyContinue
        continue
    }
    try {
        # Also stop children (e.g. node under npm, uvicorn reloader)
        $children = Get-CimInstance Win32_Process -Filter "ParentProcessId=$procId" -ErrorAction SilentlyContinue
        foreach ($c in $children) {
            $childProc = Get-Process -Id $c.ProcessId -ErrorAction SilentlyContinue
            if ($childProc -and ($allowedNames -contains $childProc.ProcessName.ToLowerInvariant())) {
                Stop-Process -Id $c.ProcessId -Force -ErrorAction SilentlyContinue
            }
        }
        Stop-Process -Id $procId -Force -ErrorAction Stop
        Write-Host "Stopped PID $procId ($name)"
    } catch {
        Write-Warning "Could not stop PID $procId : $_"
    }
    Remove-Item -Force $f.FullName -ErrorAction SilentlyContinue
}

Write-Host "stop_demo complete"
exit 0
