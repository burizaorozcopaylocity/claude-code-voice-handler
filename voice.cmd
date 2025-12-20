@echo off
REM Quick voice control for Windows
REM Usage: voice [on|off|status]

setlocal
set "SCRIPT_DIR=%~dp0"
set "PS_SCRIPT=%SCRIPT_DIR%toggle_voice.ps1"

if "%1"=="" (
    powershell -NoProfile -ExecutionPolicy Bypass -File "%PS_SCRIPT%" -Status
    exit /b
)

if /i "%1"=="on" (
    powershell -NoProfile -ExecutionPolicy Bypass -File "%PS_SCRIPT%" -Enable
    exit /b
)

if /i "%1"=="off" (
    powershell -NoProfile -ExecutionPolicy Bypass -File "%PS_SCRIPT%" -Disable
    exit /b
)

if /i "%1"=="status" (
    powershell -NoProfile -ExecutionPolicy Bypass -File "%PS_SCRIPT%" -Status
    exit /b
)

echo Usage: voice [on^|off^|status]
exit /b 1
