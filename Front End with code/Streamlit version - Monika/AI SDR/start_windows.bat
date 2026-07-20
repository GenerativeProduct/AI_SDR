@echo off
:: Set window title and dimensions
title AI SDR Platform Launcher
mode con: cols=90 lines=25

echo =================================================================================
echo                      AI SDR PLATFORM LAUNCHER FOR WINDOWS
echo =================================================================================
echo.
echo This launcher will verify Docker Desktop, start it if needed, deploy the services,
echo and launch the application in your web browser.
echo.
echo Please wait...
echo.

:: Run the PowerShell launcher script
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0launch_windows.ps1"

if %ERRORLEVEL% neq 0 (
    echo.
    echo [ERROR] Launcher execution failed. Please check the logs above.
    echo.
    pause
    exit /b %ERRORLEVEL%
)

echo.
echo Launcher complete.
pause
