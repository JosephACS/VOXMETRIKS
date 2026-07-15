#requires -Version 5.1
<#
.SYNOPSIS
  Export demo runtime bundle (env files, duckdb, media) without printing secrets.
#>
[CmdletBinding()]
param(
    [string]$DestDir = ''
)

$ErrorActionPreference = 'Stop'
$RepoRoot = Split-Path -Parent $PSScriptRoot
if (-not $DestDir) {
    $DestDir = Join-Path (Split-Path $RepoRoot -Parent) 'VOXMETRIKS-DEMO-RUNTIME'
}

function Get-FileSha256 {
    param([string]$Path)
    return (Get-FileHash -Algorithm SHA256 -Path $Path).Hash.ToLowerInvariant()
}

function Write-Utf8NoBom {
    param([string]$Path, [string]$Content)
    $utf8 = New-Object System.Text.UTF8Encoding $false
    [System.IO.File]::WriteAllText($Path, $Content, $utf8)
}

Write-Host "Export DestDir: $DestDir"
New-Item -ItemType Directory -Force -Path $DestDir | Out-Null
$envOut = Join-Path $DestDir 'env'
$dataOut = Join-Path $DestDir 'data'
$whOut = Join-Path $dataOut 'warehouse'
$mediaOut = Join-Path $dataOut 'media'
New-Item -ItemType Directory -Force -Path $envOut, $whOut | Out-Null

$manifestEntries = @()
$shaLines = New-Object System.Collections.Generic.List[string]

# --- env copies (never print contents) ---
$backendEnvSrc = Join-Path $RepoRoot 'apps\backend\.env'
$rootEnvSrc = Join-Path $RepoRoot '.env'
$backendEnvDest = Join-Path $envOut 'backend.env'
$rootEnvDest = Join-Path $envOut 'root.env'

if (Test-Path $backendEnvSrc) {
    Copy-Item -LiteralPath $backendEnvSrc -Destination $backendEnvDest -Force
    $h = Get-FileSha256 $backendEnvDest
    $sz = (Get-Item $backendEnvDest).Length
    $manifestEntries += [pscustomobject]@{ path = 'env/backend.env'; size = $sz; sha256 = $h }
    $shaLines.Add("$h  env/backend.env")
    Write-Host 'OK copied env/backend.env (contents not printed)'
} else {
    Write-Host 'SKIP apps/backend/.env not found'
}

if (Test-Path $rootEnvSrc) {
    Copy-Item -LiteralPath $rootEnvSrc -Destination $rootEnvDest -Force
    $h = Get-FileSha256 $rootEnvDest
    $sz = (Get-Item $rootEnvDest).Length
    $manifestEntries += [pscustomobject]@{ path = 'env/root.env'; size = $sz; sha256 = $h }
    $shaLines.Add("$h  env/root.env")
    Write-Host 'OK copied env/root.env (contents not printed)'
} else {
    Write-Host 'SKIP root .env not found'
}

# --- DuckDB safe copy (CHECKPOINT then copy) ---
$duckSrc = Join-Path $RepoRoot 'data\warehouse\voxmetrik.duckdb'
$duckDest = Join-Path $whOut 'voxmetrik.duckdb'
if (-not (Test-Path $duckSrc)) {
    Write-Error "Missing source duckdb: $duckSrc"
    exit 1
}

$pythonCandidates = @(
    (Join-Path $RepoRoot 'apps\backend\.venv\Scripts\python.exe'),
    'python'
)
$py = $null
foreach ($c in $pythonCandidates) {
    if ($c -eq 'python') {
        if (Get-Command python -ErrorAction SilentlyContinue) { $py = 'python'; break }
    } elseif (Test-Path $c) { $py = $c; break }
}

$checkpointOk = $false
if ($py) {
    $duckSrcPy = $duckSrc -replace '\\', '/'
    $code = @"
import duckdb, sys
src = r'''$duckSrc'''
try:
    con = duckdb.connect(src)
    con.execute('CHECKPOINT')
    con.close()
    print('CHECKPOINT_OK')
except Exception as e:
    print('CHECKPOINT_FAIL:' + type(e).__name__)
    sys.exit(2)
"@
    $tmpPy = Join-Path $env:TEMP ("vox_checkpoint_{0}.py" -f [guid]::NewGuid().ToString('N'))
    Write-Utf8NoBom -Path $tmpPy -Content $code
    try {
        $out = & $py $tmpPy 2>&1 | Out-String
        if ($LASTEXITCODE -eq 0 -and $out -match 'CHECKPOINT_OK') { $checkpointOk = $true }
    } finally {
        Remove-Item -Force $tmpPy -ErrorAction SilentlyContinue
    }
}

try {
    if ($checkpointOk) {
        Copy-Item -LiteralPath $duckSrc -Destination $duckDest -Force
    } else {
        # Attempt Copy-Item anyway; report locked on failure
        Copy-Item -LiteralPath $duckSrc -Destination $duckDest -Force
    }
} catch {
    $msg = $_.Exception.Message
    if ($msg -match 'being used by another process|cannot access|IOException|locking|locked') {
        Write-Error 'DB_LOCKED — stop the demo backend (.\scripts\stop_demo.ps1) and retry export.'
        exit 3
    }
    Write-Error "DuckDB copy failed: $msg"
    exit 1
}

# Also try robocopy /J for unbuffered copy if Copy-Item produced 0-byte somehow
if (-not (Test-Path $duckDest) -or ((Get-Item $duckDest).Length -lt 1)) {
    $null = robocopy (Split-Path $duckSrc -Parent) $whOut (Split-Path $duckSrc -Leaf) /J /NFL /NDL /NJH /NJS /NC /NS
    if (-not (Test-Path $duckDest)) {
        Write-Error 'DB_LOCKED or copy failed — duckdb dest missing after robocopy.'
        exit 3
    }
}

$duckHash = Get-FileSha256 $duckDest
$duckSize = (Get-Item $duckDest).Length
$manifestEntries += [pscustomobject]@{ path = 'data/warehouse/voxmetrik.duckdb'; size = $duckSize; sha256 = $duckHash }
$shaLines.Add("$duckHash  data/warehouse/voxmetrik.duckdb")
Write-Host "OK duckdb copied size=$duckSize sha256=$duckHash"

# --- media recursive ---
$mediaSrc = Join-Path $RepoRoot 'data\media'
if (Test-Path $mediaSrc) {
    New-Item -ItemType Directory -Force -Path $mediaOut | Out-Null
    Copy-Item -Path (Join-Path $mediaSrc '*') -Destination $mediaOut -Recurse -Force -ErrorAction SilentlyContinue
    $mediaFiles = Get-ChildItem -Path $mediaOut -Recurse -File -ErrorAction SilentlyContinue
    foreach ($mf in $mediaFiles) {
        $rel = 'data/media/' + ($mf.FullName.Substring($mediaOut.Length).TrimStart('\', '/') -replace '\\', '/')
        $h = Get-FileSha256 $mf.FullName
        $manifestEntries += [pscustomobject]@{ path = $rel; size = $mf.Length; sha256 = $h }
        $shaLines.Add("$h  $rel")
    }
    Write-Host "OK media copied files=$($mediaFiles.Count)"
} else {
    Write-Host 'SKIP data/media not present'
}

# --- manifest + sums + restore instructions ---
$manifest = [ordered]@{
    exported_at = (Get-Date).ToUniversalTime().ToString('o')
    repo_name   = Split-Path $RepoRoot -Leaf
    files       = @($manifestEntries | ForEach-Object {
        [ordered]@{ path = $_.path; size = $_.size; sha256 = $_.sha256 }
    })
}
$manifestPath = Join-Path $DestDir 'manifest.json'
$manifestJson = $manifest | ConvertTo-Json -Depth 6
Write-Utf8NoBom -Path $manifestPath -Content $manifestJson

$sumsPath = Join-Path $DestDir 'SHA256SUMS.txt'
Write-Utf8NoBom -Path $sumsPath -Content (($shaLines -join "`n") + "`n")

$restoreTxt = @"
VOXMETRIKS DEMO RUNTIME — RESTORE INSTRUCTIONS
==============================================

This bundle contains local demo runtime files (env templates/secrets copies,
DuckDB warehouse, optional media). Do NOT commit this folder to Git.
Do NOT print or share env file contents.

Default location sibling of repo:
  ..\VOXMETRIKS-DEMO-RUNTIME\

Restore into a clone of the repo:

  .\scripts\restore_demo_runtime.ps1 -SourceDir "<path-to-this-folder>" -RepoRoot "<path-to-voxmetriks>"

What gets restored:
  env/backend.env  ->  apps/backend/.env
  env/root.env     ->  .env   (repo root), if present in the bundle
  data/warehouse/voxmetrik.duckdb
  data/media/      (if present)

Integrity:
  SHA256SUMS.txt is verified before overwrite.
  Existing destinations are copied to *.bak.<TIMESTAMP> first.

After restore:
  1. .\scripts\setup_demo.ps1
  2. .\scripts\start_demo.ps1
  3. .\scripts\verify_demo.ps1

Never paste DEMO_ACCOUNT_PASSWORD into chat, docs, or screenshots.
"@
Write-Utf8NoBom -Path (Join-Path $DestDir 'RESTORE-INSTRUCTIONS.txt') -Content $restoreTxt

$fileCount = (Get-ChildItem -Path $DestDir -Recurse -File | Measure-Object).Count
$totalSize = (Get-ChildItem -Path $DestDir -Recurse -File | Measure-Object -Property Length -Sum).Sum
Write-Host "EXPORT_OK dest=$DestDir files=$fileCount bytes=$totalSize duckdb_sha256=$duckHash"
exit 0
