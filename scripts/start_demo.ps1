#requires -Version 5.1
[CmdletBinding()]
param()
$ErrorActionPreference = 'Stop'
[Console]::Error.WriteLine('DEPRECATED: start_demo.ps1 -> use .\scripts\start.ps1')
& (Join-Path $PSScriptRoot 'start.ps1') @args
exit $LASTEXITCODE