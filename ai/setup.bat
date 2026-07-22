@echo off

echo ======================================
echo Neighbourhood Watchdog Installer
echo ======================================

echo Checking for Python...

python --version >nul 2>&1

@REM Python found
IF %ERRORLEVEL% EQU 0 (
    echo Python detected.
    echo Launching installer...
    python "%~dp0bootstrap.py"
    pause
    exit /b 0
)

echo Python not found.
echo Attempting installation using Winget...

winget install Python.Python.3.12 --accept-package-agreements --accept-source-agreements

@REM Did Winget fail?
IF %ERRORLEVEL% NEQ 0 (
    echo Failed to install Python using Winget.
    echo Please install Python 3.12 manually and run setup.bat again.
    pause
    exit /b 1
)

echo ======================================
echo Python installed successfully!
echo Restarting installer...
echo ======================================

REM Start a NEW copy of this batch file
start "" "%~f0"

REM Close this copy
exit /b 0