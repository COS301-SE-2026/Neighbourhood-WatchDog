@REM SUMMARY: Start script AND check if Python is installed
@echo off
@REM Only print what we want the user to see

echo ======================================
echo Neighbourhood Watchdog Installer
echo ======================================

python --version >nul 2>&1
@REM check the previous command, if the output errorlvl is != 0 then we need to install python (0 means success and  != 0 means failure)
IF %ERRORLEVEL% NEQ 0 (
    echo Python not found.
    echo Attempting installation...

    winget install Python.Python.3.12
    @REM Check if the install worked, if failed we print that they need to install python manually
    IF %ERRORLEVEL% NEQ 0 (
        echo Winget failed.
        echo Please install Python manually or try again.
        @REM This lets the user see the error rather than closing the whole application
        pause
        exit
    )
)
@REM Now we run the python script
python bootstrap.py