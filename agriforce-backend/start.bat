@echo off
title AgriForce Backend Server
color 0A

echo.
echo  =========================================
echo    AgriForce Backend API  ^|  FastAPI
echo  =========================================
echo.

:: ── Step 1: Check Python ────────────────────────────────────
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo  [ERROR] Python not found. Please install Python 3.11+
    pause
    exit /b 1
)

:: ── Step 2: Create venv if missing ──────────────────────────
if not exist ".venv" (
    echo  [INFO] Creating virtual environment...
    python -m venv .venv
    if %errorlevel% neq 0 (
        echo  [ERROR] Failed to create virtual environment.
        pause
        exit /b 1
    )
    echo  [OK]   Virtual environment created.
)

:: ── Step 3: Activate venv ───────────────────────────────────
echo  [INFO] Activating virtual environment...
call .venv\Scripts\activate.bat

:: ── Step 4: Install / upgrade dependencies ──────────────────
echo  [INFO] Installing dependencies from requirements.txt...
pip install -q -r requirements.txt
if %errorlevel% neq 0 (
    echo  [ERROR] Failed to install dependencies.
    pause
    exit /b 1
)
echo  [OK]   Dependencies ready.

:: ── Step 5: Check .env exists ───────────────────────────────
if not exist ".env" (
    echo  [WARN] .env file not found! Copy .env.example and fill in your values.
    pause
    exit /b 1
)

:: ── Step 6: Start Uvicorn ───────────────────────────────────
echo.
echo  [OK]   Starting server at http://localhost:8000
echo  [OK]   Swagger UI  ->  http://localhost:8000/docs
echo  [OK]   ReDoc       ->  http://localhost:8000/redoc
echo.
echo  Press Ctrl+C to stop the server.
echo  =========================================
echo.

uvicorn main:app --host 0.0.0.0 --port 8000 --reload

:: ── On exit ─────────────────────────────────────────────────
echo.
echo  [INFO] Server stopped.
pause
