@echo off
title AgriForce — Full Stack Launcher
color 0A

echo.
echo  =========================================================
echo    AgriForce  ^|  Full-Stack Launcher
echo    Backend  : http://localhost:8000
echo    Frontend : http://localhost:5500
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

:: ── Step 2: Create venv in backend folder if missing ──────────
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

:: ── Step 3: Install / upgrade dependencies ────────────────────
echo  [INFO] Installing backend dependencies...
call agriforce-backend\.venv\Scripts\activate.bat
pip install -q -r agriforce-backend\requirements.txt
if %errorlevel% neq 0 (
    echo  [ERROR] Failed to install dependencies.
    pause
    exit /b 1
)
echo  [OK]   Dependencies ready.

:: ── Step 4: Check .env exists ─────────────────────────────────
if not exist "agriforce-backend\.env" (
    echo  [WARN] agriforce-backend\.env not found!
    echo         Please create it with your DB credentials before starting.
    pause
    exit /b 1
)
echo  [OK]   .env found.

:: ── Step 5: Launch Backend (new window) ───────────────────────
echo.
echo  [INFO] Starting FastAPI backend in a new window...
start "AgriForce Backend (port 8000)" cmd /k "cd /d %~dp0agriforce-backend && .venv\Scripts\activate.bat && uvicorn main:app --host 0.0.0.0 --port 8000 --reload"

:: Brief pause so backend window appears first
timeout /t 2 /nobreak >nul

:: ── Step 6: Launch Frontend (new window) ──────────────────────
echo  [INFO] Starting frontend static server in a new window...
start "AgriForce Frontend (port 5500)" cmd /k "cd /d %~dp0 && python -m http.server 5500"

:: ── Done ──────────────────────────────────────────────────────
echo.
echo  =========================================================
echo  [OK]   Both servers are starting up!
echo.
echo    Backend  API   ->  http://localhost:8000
echo    Swagger  UI    ->  http://localhost:8000/docs
echo    Frontend App   ->  http://localhost:5500
echo.
echo  Close the individual server windows to stop each service.
echo  =========================================================
echo.
pause
