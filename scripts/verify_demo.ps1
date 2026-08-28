#requires -Version 5.1
[CmdletBinding()]
param()
$ErrorActionPreference = 'Stop'
[Console]::Error.WriteLine('DEPRECATED: verify_demo.ps1 -> use .\scripts\verify.ps1')
& (Join-Path $PSScriptRoot 'verify.ps1') @args
exit $LASTEXITCODE