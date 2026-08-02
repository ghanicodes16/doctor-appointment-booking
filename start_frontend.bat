@echo off
REM ============================================================
REM  Start the React frontend on http://127.0.0.1:5173
REM  Run this from the project root (or double-click it).
REM ============================================================
cd /d "%~dp0frontend"

if not exist "node_modules" (
    echo Installing dependencies...
    call npm install
)

echo Starting the frontend on http://localhost:5173/doctor-appointment-booking/  (Ctrl+C to stop)
call npm run dev
