@echo off
REM ============================================================
REM  Start the FastAPI backend on http://127.0.0.1:8000
REM  Run this from the project root (or double-click it).
REM ============================================================
cd /d "%~dp0backend"

REM Create the virtual environment if it does not exist yet.
if not exist ".venv" (
    echo Creating virtual environment...
    python -m venv .venv
    .venv\Scripts\pip install -r requirements.txt
)

echo Starting the backend on http://127.0.0.1:8000  (Ctrl+C to stop)
.venv\Scripts\python -m uvicorn app.main:app --reload --port 8000
