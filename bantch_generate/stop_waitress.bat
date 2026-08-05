@echo off
setlocal EnableExtensions

cd /d "%~dp0"
set "PID_FILE=%~dp0.waitress.pid"

if not exist "%PID_FILE%" (
  echo [INFO] PID file was not found. YCC-Edit may already be stopped.
  exit /b 0
)

set /p APP_PID=<"%PID_FILE%"
if not defined APP_PID (
  del /q "%PID_FILE%" >nul 2>nul
  echo [INFO] Empty PID file removed.
  exit /b 0
)

powershell -NoProfile -Command "$process=Get-CimInstance Win32_Process -Filter 'ProcessId=%APP_PID%' -ErrorAction SilentlyContinue; if (-not $process) { exit 2 }; $listener=Get-NetTCPConnection -LocalPort 5002 -State Listen -ErrorAction SilentlyContinue | Where-Object { $_.OwningProcess -eq %APP_PID% }; if (-not $listener -or $process.CommandLine -notmatch 'waitress' -or $process.CommandLine -notmatch 'app:app') { exit 3 }; Stop-Process -Id %APP_PID% -Force; exit 0"
set "STOP_RESULT=%ERRORLEVEL%"

if "%STOP_RESULT%"=="2" (
  del /q "%PID_FILE%" >nul 2>nul
  echo [INFO] Process %APP_PID% was not running. Stale PID file removed.
  exit /b 0
)

if "%STOP_RESULT%"=="3" (
  echo [ERROR] PID %APP_PID% does not belong to this Waitress app. Nothing was stopped.
  echo Delete %PID_FILE% manually only after confirming the recorded PID is stale.
  pause
  exit /b 1
)

if not "%STOP_RESULT%"=="0" (
  echo [ERROR] Failed to stop PID %APP_PID%.
  pause
  exit /b 1
)

del /q "%PID_FILE%" >nul 2>nul
echo [OK] YCC-Edit stopped. PID: %APP_PID%
exit /b 0
