@echo off
REM VOXMETRIKS — Iniciar entorno de desarrollo local (Windows)
setlocal
set ROOT=%~dp0
cd /d "%ROOT%"

echo.
echo ========================================================================
echo   VOXMETRIKS - Desarrollo local
echo ========================================================================
echo.

if not exist "%ROOT%venv\Scripts\python.exe" (
    echo [ERROR] No existe el entorno virtual. Ejecuta primero:
    echo   python -m venv venv
    echo   venv\Scripts\pip install -r backend\requirements.txt
    pause
    exit /b 1
)

if not exist "%ROOT%data\warehouse\voxmetrik.duckdb" (
    echo [INFO] Base de datos no encontrada. Ejecutando pipeline ELT...
    call "%ROOT%venv\Scripts\python.exe" "%ROOT%elt\pipelines\elt_pipeline.py"
    if errorlevel 1 (
        echo [ERROR] El pipeline ELT fallo.
        pause
        exit /b 1
    )
)

echo [1/2] Iniciando backend API en http://127.0.0.1:8000 ...
start "VOXMETRIKS API" cmd /k "cd /d \"%ROOT%backend\" && \"%ROOT%venv\Scripts\uvicorn.exe\" app.main:app --host 127.0.0.1 --port 8000 --reload"

echo [2/2] Iniciando frontend Angular en http://127.0.0.1:4200 ...
start "VOXMETRIKS Frontend" cmd /k "cd /d \"%ROOT%frontend\" && npm start -- --host 127.0.0.1 --port 4200"

echo.
echo Listo. Abre:
echo   Frontend : http://127.0.0.1:4200
echo   API docs : http://127.0.0.1:8000/docs
echo   Health   : http://127.0.0.1:8000/health
echo.
pause
