@echo off
setlocal
rem "where python" matches the Microsoft Store stub in WindowsApps, which isn't
rem a real Python — find_python.ps1 probes by actually running it.
call :find_python
if not "%PY%"=="" goto :run

echo Python not found.
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0Scripts\install_python.ps1"
if errorlevel 1 (
    echo.
    echo Automatic install failed. Get Python from https://www.python.org/downloads/
    echo ^(tick "Add Python to PATH" in the installer^), then run App.bat again.
    pause
    exit /b 1
)
rem Installer updated PATH for future sessions; look again so this run works.
call :find_python
if "%PY%"=="" (
    echo.
    echo Python installed. Close this window and run App.bat again ^(PATH needs to refresh^).
    pause
    exit /b 0
)

:run
"%PY%" "%~dp0Scripts\wiztree_analyst_gui.py"
if errorlevel 1 pause
exit /b 0

:find_python
set "PY="
for /f "delims=" %%i in ('powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0Scripts\find_python.ps1" 2^>nul') do set "PY=%%i"
exit /b 0
