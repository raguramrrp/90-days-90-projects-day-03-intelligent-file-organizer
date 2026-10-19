@echo off
setlocal

echo ======================================================================
echo    Context-Aware Desktop File Organization Automation
echo    Launching Graphical User Interface (Tkinter)
echo ======================================================================
echo.

if not exist .venv\Scripts\python.exe (
    echo [ERROR] Virtual environment not detected at .venv
    echo Please execute setup.bat first to configure Python dependencies.
    echo.
    pause
    exit /b 1
)

set PYTHONPATH=%~dp0;%PYTHONPATH%

echo Starting File Organizer UI...
echo (Close the application window or press Ctrl+C in this terminal to exit)
echo.

.\.venv\Scripts\python src\main.py --gui

if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Application exited unexpectedly with code %errorlevel%.
    pause
)
