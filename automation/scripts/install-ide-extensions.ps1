# Instala las extensiones recomendadas de Voxmetriks en Cursor o VS Code.
# Uso (PowerShell, desde la raiz del repo):
#   .\scripts\install-ide-extensions.ps1
#
# Si falla, abre Cursor -> Extensions (Ctrl+Shift+X) e instala por nombre.

$ErrorActionPreference = "Continue"

$extensions = @(
  "Angular.ng-template",
  "esbenp.prettier-vscode",
  "dbaeumer.vscode-eslint",
  "formulahendry.auto-rename-tag",
  "formulahendry.auto-close-tag",
  "ecmel.vscode-html-css",
  "ms-python.python",
  "ms-python.vscode-pylance",
  "ms-python.debugpy",
  "mtxr.sqltools",
  "Evidence.sqltools-duckdb-driver",
  "RandomFractalsInc.duckdb-sql-tools",
  "humao.rest-client",
  "ms-azuretools.vscode-docker",
  "usernamehw.errorlens",
  "eamodio.gitlens"
)

function Find-EditorCli {
  $candidates = @()
  $cursorCmd = Get-Command cursor -ErrorAction SilentlyContinue
  if ($cursorCmd) { $candidates += $cursorCmd.Source }
  $codeCmd = Get-Command code -ErrorAction SilentlyContinue
  if ($codeCmd) { $candidates += $codeCmd.Source }
  $candidates += "$env:LOCALAPPDATA\Programs\cursor\resources\app\bin\cursor.cmd"
  $candidates += "$env:LOCALAPPDATA\Programs\Microsoft VS Code\bin\code.cmd"

  foreach ($path in $candidates) {
    if ($path -and (Test-Path $path)) { return $path }
  }
  return $null
}

$cli = Find-EditorCli
if (-not $cli) {
  Write-Host ""
  Write-Host "No encontre 'cursor' ni 'code' en PATH." -ForegroundColor Yellow
  Write-Host "Instala manualmente desde Cursor -> Extensions (Ctrl+Shift+X):" -ForegroundColor Yellow
  foreach ($ext in $extensions) { Write-Host "  - $ext" }
  Write-Host ""
  exit 1
}

Write-Host "Usando: $cli" -ForegroundColor Cyan
Write-Host ""

$ok = 0
$fail = 0
foreach ($ext in $extensions) {
  Write-Host "Instalando $ext ..."
  & $cli --install-extension $ext --force 2>&1 | Out-Null
  if ($LASTEXITCODE -eq 0) {
    $ok++
    Write-Host "  OK" -ForegroundColor Green
  } else {
    $fail++
    Write-Host "  Fallo (instala manual: busca '$ext' en Extensions)" -ForegroundColor Red
  }
}

Write-Host ""
Write-Host "Listo: $ok instaladas, $fail fallaron." -ForegroundColor Cyan
Write-Host "Recarga Cursor: Ctrl+Shift+P -> Developer: Reload Window"
