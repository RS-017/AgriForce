@echo off
title AgriForce — Full Stack Launcher
color 0A

echo.
echo  =========================================================
echo    AgriForce  ^|  Full-Stack Launcher
echo  =========================================================
echo.

:: ── Step 1: Check Python ──────────────────────────────────────
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo  [ERROR] Python not found. Please install Python 3.11+
    pause
    exit /b 1
)
echo  [OK]   Python found.

:: ── Step 2: Check for port conflicts ─────────────────────────
netstat -ano | findstr ":8000 " >nul 2>&1
if %errorlevel% equ 0 (
    echo  [WARN] Port 8000 is already in use. Backend may already be running.
)
netstat -ano | findstr ":3000 " >nul 2>&1
if %errorlevel% equ 0 (
    echo  [WARN] Port 3000 is already in use. Frontend may already be running.
)

:: ── Step 3: Create venv if missing ───────────────────────────
if not exist "agriforce-backend\.venv" (
    echo  [INFO] Creating virtual environment...
    python -m venv agriforce-backend\.venv
    if %errorlevel% neq 0 (
        echo  [ERROR] Failed to create virtual environment.
        pause
        exit /b 1
    )
    echo  [OK]   Virtual environment created.
)

:: ── Step 4: Install / upgrade dependencies ───────────────────
echo  [INFO] Installing backend dependencies (may take a moment)...
call agriforce-backend\.venv\Scripts\activate.bat
pip install -q -r agriforce-backend\requirements.txt
if %errorlevel% neq 0 (
    echo  [ERROR] Failed to install dependencies.
    pause
    exit /b 1
)
echo  [OK]   Dependencies ready.

:: ── Step 5: Check .env ───────────────────────────────────────
if not exist "agriforce-backend\.env" (
    echo  [WARN] agriforce-backend\.env not found!
    echo         Please create it with your DB credentials.
    pause
    exit /b 1
)
echo  [OK]   .env found.

:: ── Step 6: Launch Backend in new window ─────────────────────
echo  [INFO] Starting FastAPI backend on port 8000...
start "AgriForce Backend ^| port 8000" cmd /k ^
  "cd /d "%~dp0agriforce-backend" && .venv\Scripts\activate.bat && uvicorn main:app --host 0.0.0.0 --port 8000 --reload"

:: Wait for backend to be ready
timeout /t 3 /nobreak >nul

:: ── Step 7: Launch Frontend in new window ────────────────────
echo  [INFO] Starting frontend server on port 3000...
start "AgriForce Frontend ^| port 3000" cmd /k ^
  "cd /d "%~dp0" && python -m http.server 3000"

:: Wait for frontend to bind
timeout /t 2 /nobreak >nul

:: ── Step 8: Open browser automatically ───────────────────────
echo  [INFO] Opening browser...
start "" "http://localhost:3000/index.html"

:: ── Done ─────────────────────────────────────────────────────
echo.
echo  =========================================================
echo  [OK]   AgriForce is running!
echo.
echo    Frontend App   ->  http://localhost:3000/index.html
echo    Backend  API   ->  http://localhost:8000
echo    Swagger  UI    ->  http://localhost:8000/docs
echo.
echo  To stop: close the Backend and Frontend server windows.
echo  =========================================================
echo.
pause
