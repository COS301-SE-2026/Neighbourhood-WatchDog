@echo off
echo Neighbourhood Watchdog Installer starting
echo Checking for Python...

python --version >nul 2>&1

IF %ERRORLEVEL% NEQ 0 (
    echo Python not found.
    echo Attempting installation using Winget...

    @REM Try python installation with winget
    winget install Python.Python.3.12 --accept-package-agreements --accept-source-agreements

    @REM Did Winget fail?
    IF %ERRORLEVEL% NEQ 0 (
        echo Winget installation failed.
        echo Attempting direct download from python.org...

        @REM Download the installer
        powershell -Command "Invoke-WebRequest -Uri https://www.python.org/ftp/python/3.12.11/python-3.12.11-amd64.exe -OutFile python-installer.exe"

        @REM Make sure the download succeeded
        IF NOT EXIST python-installer.exe (
            echo Failed to download the Python installer.
            pause
            exit /b 1
        )

        echo Installing Python...

        @REM Install silently
        python-installer.exe /quiet InstallAllUsers=0 PrependPath=1 Include_test=0

        echo Cleaning up installer...
        del python-installer.exe

    )

    echo Verifying Python installation...

    python --version >nul 2>&1

    IF %ERRORLEVEL% NEQ 0 (
        echo Python installation failed.
        pause
        exit /b 1
    )
)

echo Python is ready.
echo Launching bootstrap...

python "%~dp0bootstrap.py"

pause