@echo off
setlocal

cd /d "%~dp0"
set "PYTHON_EXE=%~dp0..\.qtvenv\Scripts\python.exe"

if not exist "%PYTHON_EXE%" (
    echo Qt Python environment was not found:
    echo %PYTHON_EXE%
    echo.
    echo Create it first with:
    echo python -m venv ..\.qtvenv
    echo ..\.qtvenv\Scripts\python.exe -m pip install -r requirements.txt
    echo.
    pause
    exit /b 1
)

"%PYTHON_EXE%" "%~dp0project_timer.py"

if errorlevel 1 (
    echo.
    echo Project Timer closed with an error.
    pause
)
