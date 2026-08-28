#requires -Version 5.1
[CmdletBinding()]
param()
$ErrorActionPreference = 'Stop'
[Console]::Error.WriteLine('DEPRECATED: setup_demo.ps1 -> use .\scripts\setup.ps1')
& (Join-Path $PSScriptRoot 'setup.ps1') @args
exit $LASTEXITCODE