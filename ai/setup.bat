@echo off

echo ======================================
echo Neighbourhood Watchdog Installer
echo ======================================
echo.

echo Checking for Python...

python --version >nul 2>&1

IF %ERRORLEVEL% NEQ 0 ( @REM Was a python version
    echo Python not found.
    echo Attempting installation with Winget...

    winget install Python.Python.3.12 --accept-package-agreements --accept-source-agreements @REM download python with winget

    IF %ERRORLEVEL% NEQ 0 ( @REM Check if installation succeeded
        echo Winget installation failed.
        echo Direct download fallback not yet implemented.
        @REM TODO: implement fallback download
        pause
        exit /b 1
    )

    echo Verifying installation...

    python --version >nul 2>&1
    @REM check version one last time
    IF %ERRORLEVEL% NEQ 0 (
        echo Python installation could not be verified.
        pause
        exit /b 1
    )
)

echo Python found.
echo Starting bootstrap...

python "%~dp0bootstrap.py"