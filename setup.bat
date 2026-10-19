@echo off
setlocal EnableDelayedExpansion

echo ======================================================================
echo    Context-Aware Desktop File Organization Automation - Setup
echo    Day 3 - 90 Days 90 Projects Challenge
echo ======================================================================
echo.

:: 1. Detect Python runtime
echo [1/5] Checking for Python installation...
set PYTHON_CMD=

py --version >nul 2>&1
if %errorlevel% equ 0 (
    set PYTHON_CMD=py
    goto PYTHON_FOUND
)

python --version >nul 2>&1
if %errorlevel% equ 0 (
    set PYTHON_CMD=python
    goto PYTHON_FOUND
)

echo [ERROR] No compatible Python installation found on system PATH.
echo Please install Python 3.10+ from https://www.python.org/
pause
exit /b 1

:PYTHON_FOUND
echo Found Python via: %PYTHON_CMD%
%PYTHON_CMD% --version

:: 2. Create project-specific virtual environment
echo.
echo [2/5] Configuring virtual environment (.venv)...
if not exist .venv (
    echo Creating virtual environment at .venv...
    %PYTHON_CMD% -m venv .venv
    if %errorlevel% neq 0 (
        echo [ERROR] Failed to create virtual environment.
        pause
        exit /b 1
    )
    echo Virtual environment created.
) else (
    echo Existing .venv directory detected.
)

:: 3. Install project dependencies
echo.
echo [3/5] Installing dependencies from requirements.txt...
.\.venv\Scripts\python -m pip install --upgrade pip >nul 2>&1
.\.venv\Scripts\pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo [ERROR] Failed to install dependencies.
    pause
    exit /b 1
)
echo Dependencies installed successfully.

:: 4. Ensure directories exist
echo.
echo [4/5] Initializing local directories...
if not exist data mkdir data
if not exist data\sample_clutter mkdir data\sample_clutter
if not exist screenshots mkdir screenshots
if not exist logs mkdir logs

:: 5. Generate sample benchmark downloads clutter
echo.
echo [5/5] Generating synthetic downloads clutter for safe demonstration...
.\.venv\Scripts\python scripts\generate_sample_data.py
if %errorlevel% neq 0 (
    echo [WARNING] Sample data generator completed with warnings.
)

echo.
echo ======================================================================
echo    SETUP COMPLETE! You are ready to run the project.
echo    To launch the interactive GUI, run:  run.bat
echo    To execute the automated test suite: test.bat
echo    To build standalone Windows .exe:    build_exe.bat
echo ======================================================================
echo.
pause
