#requires -Version 5.1
<#
.SYNOPSIS
  DEPRECATED compatibility shim. Prefer scripts/runtime_common.ps1.
#>
[Console]::Error.WriteLine('DEPRECATED: demo_runtime_common.ps1 -> use .\scripts\runtime_common.ps1')
. (Join-Path $PSScriptRoot 'runtime_common.ps1')

# Legacy Demo-* wrappers for callers that still use the old helper names.
function Normalize-DemoIdentityText { param([string]$Value) Normalize-RuntimeIdentityText -Value $Value }
function Test-DemoPathMatch { param([string]$Candidate, [string]$ExpectedLower) Test-RuntimePathMatch -Candidate $Candidate -ExpectedLower $ExpectedLower }
function Get-DemoProcessHandleInfo { param([int]$ProcessId) Get-RuntimeProcessHandleInfo -ProcessId $ProcessId }
function Get-DemoProcessWmiInfo { param([int]$ProcessId) Get-RuntimeProcessWmiInfo -ProcessId $ProcessId }
function Test-DemoHttpStatus200 { param([string]$Url, [int]$TimeoutSec = 3) Test-RuntimeHttpStatus200 -Url $Url -TimeoutSec $TimeoutSec }
function Test-DemoProcessRunning { param([int]$ProcessId) Test-RuntimeProcessRunning -ProcessId $ProcessId }
function Test-DemoExecutablePathEquals { param([string]$Left, [string]$Right) Test-RuntimeExecutablePathEquals -Left $Left -Right $Right }
function Test-DemoArtifactPathAllowed { param([string]$ArtifactPath, [string]$PidDir) Test-RuntimeArtifactPathAllowed -ArtifactPath $ArtifactPath -PidDir $PidDir }
function Start-DemoDetachedProcess {
    param(
        [Parameter(Mandatory = $true)][string]$FilePath,
        [Parameter(Mandatory = $true)][string[]]$ArgumentList,
        [Parameter(Mandatory = $true)][string]$WorkingDirectory,
        [Parameter(Mandatory = $true)][string]$StdoutLog,
        [Parameter(Mandatory = $true)][string]$StderrLog
    )
    Start-RuntimeDetachedProcess -FilePath $FilePath -ArgumentList $ArgumentList -WorkingDirectory $WorkingDirectory -StdoutLog $StdoutLog -StderrLog $StderrLog
}
function Show-DemoLogTail { param([string]$StdoutLog, [string]$StderrLog, [int]$Tail = 40) Show-RuntimeLogTail -StdoutLog $StdoutLog -StderrLog $StderrLog -Tail $Tail }
function Get-DemoOwnedRecordsArray { param($OwnedList) Get-RuntimeOwnedRecordsArray -OwnedList $OwnedList }
function Get-DemoBackendShutdownRequestPath { param([Parameter(Mandatory = $true)][string]$PidDir) Get-RuntimeBackendShutdownRequestPath -PidDir $PidDir }
function Clear-DemoBackendShutdownRequest { param([Parameter(Mandatory = $true)][string]$PidDir) Clear-RuntimeBackendShutdownRequest -PidDir $PidDir }
function Request-DemoBackendGracefulShutdown { param([Parameter(Mandatory = $true)][string]$PidDir) Request-RuntimeBackendGracefulShutdown -PidDir $PidDir }
function Test-DemoBackendShutdownCompleteInLogs { param([Parameter(Mandatory = $true)][string]$PidDir) Test-RuntimeBackendShutdownCompleteInLogs -PidDir $PidDir }
function Wait-DemoBackendGracefulExit {
    param([Parameter(Mandatory = $true)][int]$ProcessId, [Parameter(Mandatory = $true)][string]$PidDir, [int]$TimeoutSec = 20)
    Wait-RuntimeBackendGracefulExit -ProcessId $ProcessId -PidDir $PidDir -TimeoutSec $TimeoutSec
}
function Stop-DemoBackendGracefulOrForce {
    param([Parameter(Mandatory = $true)][int]$ProcessId, [Parameter(Mandatory = $true)][string]$PidDir, [int]$TimeoutSec = 20)
    Stop-RuntimeBackendGracefulOrForce -ProcessId $ProcessId -PidDir $PidDir -TimeoutSec $TimeoutSec
}
function Stop-DemoVerifiedLauncher { param([int]$ProcessId) Stop-RuntimeVerifiedLauncher -ProcessId $ProcessId }
function Stop-DemoSessionOwnedRecords {
    param($OwnedList, [string]$PidDir = '', [int]$BackendGracefulTimeoutSec = 20, [switch]$PassThru)
    if ($PassThru) {
        return Stop-RuntimeSessionOwnedRecords -OwnedList $OwnedList -PidDir $PidDir -BackendGracefulTimeoutSec $BackendGracefulTimeoutSec -PassThru
    }
    Stop-RuntimeSessionOwnedRecords -OwnedList $OwnedList -PidDir $PidDir -BackendGracefulTimeoutSec $BackendGracefulTimeoutSec
}
function Clear-DemoSessionArtifacts {
    param([string[]]$ArtifactPaths, [string]$PidDir)
    Clear-RuntimeSessionArtifacts -ArtifactPaths $ArtifactPaths -PidDir $PidDir
}