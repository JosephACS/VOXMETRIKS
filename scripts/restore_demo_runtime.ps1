#requires -Version 5.1
<#
.SYNOPSIS
  Restore demo runtime bundle into a repo checkout. Never prints env contents.
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory = $false)]
    [string]$SourceDir = '',
    [Parameter(Mandatory = $false)]
    [string]$RepoRoot = ''
)

$ErrorActionPreference = 'Stop'

if (-not $RepoRoot) {
    $RepoRoot = Split-Path -Parent $PSScriptRoot
}
if (-not $SourceDir) {
    $SourceDir = Join-Path (Split-Path $RepoRoot -Parent) 'VOXMETRIKS-DEMO-RUNTIME'
}

if (-not (Test-Path $SourceDir)) {
    Write-Error "SourceDir not found: $SourceDir"
    exit 1
}
if (-not (Test-Path $RepoRoot)) {
    Write-Error "RepoRoot not found: $RepoRoot"
    exit 1
}

function Get-FileSha256 {
    param([string]$Path)
    return (Get-FileHash -Algorithm SHA256 -Path $Path).Hash.ToLowerInvariant()
}

function Backup-IfExists {
    param([string]$Path)
    if (-not (Test-Path -LiteralPath $Path)) { return }
    $ts = Get-Date -Format 'yyyyMMddHHmmss'
    $bak = "$Path.bak.$ts"
    Copy-Item -LiteralPath $Path -Destination $bak -Force -Recurse
    Write-Host "Backup: $bak"
}

# --- Validate SHA256SUMS ---
$sumsPath = Join-Path $SourceDir 'SHA256SUMS.txt'
if (-not (Test-Path $sumsPath)) {
    Write-Error "Missing SHA256SUMS.txt in $SourceDir"
    exit 1
}

$failures = 0
Get-Content -Path $sumsPath -Encoding UTF8 | Where-Object { $_.Trim() -ne '' } | ForEach-Object {
    $line = $_.Trim()
    if ($line -match '^([A-Fa-f0-9]{64})\s+(.+)$') {
        $expected = $Matches[1].ToLowerInvariant()
        $rel = $Matches[2].Trim() -replace '/', '\'
        $full = Join-Path $SourceDir $rel
        if (-not (Test-Path -LiteralPath $full)) {
            Write-Host "FAIL missing file for checksum: $rel"
            $script:failures++
            return
        }
        $actual = Get-FileSha256 $full
        if ($actual -ne $expected) {
            Write-Host "FAIL sha256 mismatch: $rel"
            $script:failures++
        } else {
            Write-Host "OK sha256 $rel"
        }
    }
}
if ($failures -gt 0) {
    Write-Error "SHA256SUMS validation failed ($failures). Aborting restore."
    exit 1
}

# --- Restore env ---
$backendEnvSrc = Join-Path $SourceDir 'env\backend.env'
$rootEnvSrc = Join-Path $SourceDir 'env\root.env'
$backendEnvDest = Join-Path $RepoRoot 'apps\backend\.env'
$rootEnvDest = Join-Path $RepoRoot '.env'

if (Test-Path $backendEnvSrc) {
    New-Item -ItemType Directory -Force -Path (Split-Path $backendEnvDest) | Out-Null
    Backup-IfExists $backendEnvDest
    Copy-Item -LiteralPath $backendEnvSrc -Destination $backendEnvDest -Force
    Write-Host 'OK restored apps/backend/.env (contents not printed)'
}
if (Test-Path $rootEnvSrc) {
    Backup-IfExists $rootEnvDest
    Copy-Item -LiteralPath $rootEnvSrc -Destination $rootEnvDest -Force
    Write-Host 'OK restored root .env (contents not printed)'
}

# --- Restore duckdb ---
$duckSrc = Join-Path $SourceDir 'data\warehouse\voxmetrik.duckdb'
$duckDest = Join-Path $RepoRoot 'data\warehouse\voxmetrik.duckdb'
if (Test-Path $duckSrc) {
    New-Item -ItemType Directory -Force -Path (Split-Path $duckDest) | Out-Null
    Backup-IfExists $duckDest
    # Stale sidecar files from a prior local open break DuckDB WAL replay after overwrite.
    foreach ($sidecar in @('.wal', '.tmp', '.wal.tmp')) {
        $side = $duckDest + $sidecar
        if (Test-Path -LiteralPath $side) {
            Remove-Item -LiteralPath $side -Force -ErrorAction SilentlyContinue
            Write-Host "Removed stale $($side.Substring($RepoRoot.Length).TrimStart('\','/'))"
        }
    }
    Copy-Item -LiteralPath $duckSrc -Destination $duckDest -Force
    Write-Host 'OK restored data/warehouse/voxmetrik.duckdb'
} else {
    Write-Warning 'No duckdb in SourceDir'
}

# --- Restore media ---
$mediaSrc = Join-Path $SourceDir 'data\media'
$mediaDest = Join-Path $RepoRoot 'data\media'
$mediaDestBackend = Join-Path $RepoRoot 'apps\backend\data\media'
if (Test-Path $mediaSrc) {
    if (Test-Path $mediaDest) {
        Backup-IfExists $mediaDest
        Remove-Item -LiteralPath $mediaDest -Recurse -Force -ErrorAction SilentlyContinue
    }
    New-Item -ItemType Directory -Force -Path (Split-Path $mediaDest) | Out-Null
    Copy-Item -LiteralPath $mediaSrc -Destination $mediaDest -Recurse -Force
    Write-Host 'OK restored data/media'
    # Backend serves from MEDIA_STORAGE_ROOT (often apps/backend/data/media)
    if (Test-Path $mediaDestBackend) {
        Backup-IfExists $mediaDestBackend
        Remove-Item -LiteralPath $mediaDestBackend -Recurse -Force -ErrorAction SilentlyContinue
    }
    New-Item -ItemType Directory -Force -Path (Split-Path $mediaDestBackend) | Out-Null
    Copy-Item -LiteralPath $mediaSrc -Destination $mediaDestBackend -Recurse -Force
    Write-Host 'OK restored apps/backend/data/media'
}

Write-Host "RESTORE_OK SourceDir=$SourceDir RepoRoot=$RepoRoot"
exit 0
