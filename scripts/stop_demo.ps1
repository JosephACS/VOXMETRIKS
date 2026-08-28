#requires -Version 5.1
[CmdletBinding()]
param()
$ErrorActionPreference = 'Continue'
[Console]::Error.WriteLine('DEPRECATED: stop_demo.ps1 -> use .\scripts\stop.ps1')
& (Join-Path $PSScriptRoot 'stop.ps1') @args
exit $LASTEXITCODE