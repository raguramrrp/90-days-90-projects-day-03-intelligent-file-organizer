@echo off
setlocal

echo ======================================================================
echo    Running Automated Test Suite - Intelligent File Organizer
echo ======================================================================
echo.

if not exist .venv\Scripts\pytest.exe (
    echo [ERROR] Virtual environment or pytest not found.
    echo Please execute setup.bat first.
    exit /b 1
)

echo Executing pytest suite across scanner, classifier, rules, duplicates, database, engine, and CLI...
echo.

set PYTHONPATH=%~dp0;%PYTHONPATH%

.\.venv\Scripts\pytest -v --tb=short

if %errorlevel% neq 0 (
    echo.
    echo [FAIL] One or more automated tests failed.
    exit /b %errorlevel%
)

echo.
echo [PASS] All automated tests passed successfully!
exit /b 0
