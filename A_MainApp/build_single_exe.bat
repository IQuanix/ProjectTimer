@echo off
setlocal
cd /d "%~dp0"

set "PYTHON_EXE=%~dp0..\.qtvenv\Scripts\python.exe"
set APP_NAME=Project_Timer_V1.2_pre
set APP_ICON=icons\app.ico
if not exist "%APP_ICON%" set APP_ICON=icons\time.ico
if not exist "%APP_ICON%" set APP_ICON=icons\play.ico

if not exist "%PYTHON_EXE%" (
    echo Local Qt virtual environment not found: %PYTHON_EXE%
    echo Create it first or update this script to point at your Python environment.
    pause
    exit /b 1
)

"%PYTHON_EXE%" -m PyInstaller ^
    --noconfirm ^
    --clean ^
    --windowed ^
    --name "%APP_NAME%" ^
    --distpath "%~dp0..\dist" ^
    --workpath "%~dp0..\build" ^
    --specpath "%~dp0" ^
    --icon "%APP_ICON%" ^
    --version-file "version_info.txt" ^
    project_timer.py

if errorlevel 1 (
    echo Build failed.
    pause
    exit /b 1
)

echo.
echo Built: %~dp0..\dist\%APP_NAME%\%APP_NAME%.exe
pause
