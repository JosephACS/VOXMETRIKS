@echo off
REM ============================================================================
REM VOXMETRIK_V2 - Script de Instalación Automática para Windows
REM ============================================================================
REM Este script automatiza:
REM 1. Creación del entorno virtual
REM 2. Instalación de dependencias
REM 3. Ejecución del pipeline ELT
REM ============================================================================

cls
echo.
echo ================================================================================
echo.
echo    VOXMETRIK_V2 - Instalador Automático para Windows
echo.
echo ================================================================================
echo.

REM Verificar si Python está instalado
python --version >nul 2>&1
if %errorlevel% neq 0 (
    color 4F
    echo [ERROR] Python no está instalado o no está en PATH
    echo.
    echo Descarga Python desde: https://www.python.org/downloads/
    echo IMPORTANTE: Marca "Add Python to PATH" durante la instalación
    echo.
    pause
    exit /b 1
)

echo [✓] Python detectado
python --version
echo.

REM Paso 1: Crear entorno virtual
echo [PASO 1/4] Creando entorno virtual...
if exist venv (
    echo [✓] Entorno virtual ya existe
) else (
    echo Creando venv...
    python -m venv venv
    if %errorlevel% neq 0 (
        color 4F
        echo [ERROR] No se pudo crear el entorno virtual
        pause
        exit /b 1
    )
    echo [✓] Entorno virtual creado
)
echo.

REM Paso 2: Activar entorno
echo [PASO 2/4] Activando entorno virtual...
call venv\Scripts\activate.bat
if %errorlevel% neq 0 (
    color 4F
    echo [ERROR] No se pudo activar el entorno virtual
    pause
    exit /b 1
)
echo [✓] Entorno virtual activado
echo.

REM Paso 3: Instalar dependencias
echo [PASO 3/4] Instalando dependencias...
echo Este proceso puede tardar 2-5 minutos...
echo.

pip install --upgrade pip
pip install -r requirements.txt

if %errorlevel% neq 0 (
    color 4F
    echo.
    echo [ERROR] No se pudieron instalar las dependencias
    echo Intenta manualmente:
    echo   pip install -r requirements.txt
    echo.
    pause
    exit /b 1
)

echo.
echo [✓] Dependencias instaladas exitosamente
echo.

REM Paso 4: Ejecutar pipeline
echo [PASO 4/4] Ejecutando pipeline ELT...
echo ================================================================================
echo.

python elt_pipeline.py

if %errorlevel% neq 0 (
    color 4F
    echo.
    echo [ERROR] El pipeline falló
    echo Revisa los mensajes de error arriba
    echo.
    pause
    exit /b 1
)

echo.
echo ================================================================================
echo [✓] INSTALACIÓN COMPLETADA EXITOSAMENTE
echo ================================================================================
echo.
echo Archivos creados:
echo   • data\raw\raw_spotify.csv
echo   • data\stage\raw_spotify.parquet
echo   • duckdb\voxmetrik.duckdb
echo.
echo Próximos pasos:
echo   1. Ejecutar análisis:       python analyze_warehouse.py
echo   2. Ver ejemplos de SQL:     python example_queries.py
echo   3. Leer documentación:      README.md
echo.
color 2F
echo [SUCCESS] ¡Tu Data Warehouse está listo!
color 07
echo.
pause
