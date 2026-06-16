@echo off
REM ================================================
REM  CivicAssist — Frontend Startup Script (Windows)
REM ================================================
echo.
echo  CivicAssist - Iniciando frontend...
echo  ============================================

cd /d "%~dp0..\frontend"

REM Check node
node --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Node.js no encontrado. Instale Node.js 18+
    pause
    exit /b 1
)

REM Install if needed
if not exist "node_modules" (
    echo [INFO] Instalando dependencias npm...
    npm install
)

echo [INFO] Iniciando frontend en http://localhost:3000
npm run dev

pause
