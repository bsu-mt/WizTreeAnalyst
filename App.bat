@echo off
where python >nul 2>nul
if errorlevel 1 (
    where winget >nul 2>nul
    if errorlevel 1 (
        echo Python not found and winget is unavailable. Install Python from https://www.python.org/downloads/ ^(check "Add Python to PATH"^), then run this again.
        pause
        exit /b 1
    )
    echo Python not found. Installing via winget...
    winget install -e --id Python.Python.3.12
    if errorlevel 1 (
        echo Python install failed. Install it manually from https://www.python.org/downloads/, then run this again.
        pause
        exit /b 1
    )
    echo Python installed. Please close this window and run App.bat again ^(PATH needs to refresh^).
    pause
    exit /b 0
)
python "%~dp0Scripts\wiztree_analyst_gui.py"
if errorlevel 1 pause
