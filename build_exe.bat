@echo off
setlocal

echo ======================================================================
echo    Building Standalone Windows Executable (.exe)
echo    Day 3 - 90 Days 90 Projects Challenge
echo ======================================================================
echo.

if not exist .venv\Scripts\pyinstaller.exe (
    echo [ERROR] Virtual environment or PyInstaller not detected.
    echo Please execute setup.bat first to install build dependencies.
    echo.
    pause
    exit /b 1
)

echo Compiling ContextAwareFileOrganizer.exe into dist/ folder...
echo.

.\.venv\Scripts\python scripts\build_executable.py

if %errorlevel% neq 0 (
    echo.
    echo [ERROR] PyInstaller compilation failed with code %errorlevel%.
    pause
    exit /b %errorlevel%
)

echo.
echo ======================================================================
echo    STANDALONE EXECUTABLE BUILT SUCCESSFULLY!
echo    Output Location: dist\ContextAwareFileOrganizer.exe
echo ======================================================================
echo.
pause
