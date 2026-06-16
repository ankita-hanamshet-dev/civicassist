@echo off
REM ================================================
REM  CivicAssist — Backend Startup Script (Windows)
REM ================================================
echo.
echo  CivicAssist - Iniciando backend...
echo  ============================================

cd /d "%~dp0backend"

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python no encontrado. Instale Python 3.10+
    pause
    exit /b 1
)

REM Create venv if needed
if not exist "venv" (
    echo [INFO] Creando entorno virtual...
    python -m venv venv
)

REM Activate
call venv\Scripts\activate.bat

REM Install deps
echo [INFO] Instalando dependencias...
pip install -r requirements.txt --quiet

REM Copy .env if not present
if not exist ".env" (
    if exist "..\env.example" copy "..\env.example" ".env"
    echo [WARN] Configure su ANTHROPIC_API_KEY en backend\.env
)

REM Start
echo [INFO] Iniciando FastAPI en http://localhost:8000
echo [INFO] Documentacion: http://localhost:8000/docs
echo.
python main.py

pause
