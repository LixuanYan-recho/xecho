@echo off
setlocal EnableExtensions EnableDelayedExpansion

cd /d "%~dp0"

set "APP_PORT=5002"
set "PID_FILE=%~dp0.waitress.pid"
set "LOG_DIR=%~dp0logs"
set "STDOUT_LOG=%LOG_DIR%\waitress.out.log"
set "STDERR_LOG=%LOG_DIR%\waitress.error.log"

where python >nul 2>nul
if errorlevel 1 (
  echo [ERROR] Python was not found in PATH.
  pause
  exit /b 1
)

python -c "import waitress" >nul 2>nul
if errorlevel 1 (
  echo [ERROR] Waitress is not installed.
  echo Run: python -m pip install -r requirements.txt
  pause
  exit /b 1
)

if exist "%PID_FILE%" (
  set /p EXISTING_PID=<"%PID_FILE%"
  powershell -NoProfile -Command "$process=Get-CimInstance Win32_Process -Filter 'ProcessId=!EXISTING_PID!' -ErrorAction SilentlyContinue; $listener=Get-NetTCPConnection -LocalPort %APP_PORT% -State Listen -ErrorAction SilentlyContinue | Where-Object { $_.OwningProcess -eq !EXISTING_PID! }; if ($process -and $listener -and $process.CommandLine -match 'waitress' -and $process.CommandLine -match 'app:app') { exit 0 } else { exit 1 }"
  if not errorlevel 1 (
    echo [INFO] YCC-Edit is already running. PID: !EXISTING_PID!
    exit /b 0
  )
  del /q "%PID_FILE%" >nul 2>nul
)

powershell -NoProfile -Command "if (Get-NetTCPConnection -LocalPort %APP_PORT% -State Listen -ErrorAction SilentlyContinue) { exit 0 } else { exit 1 }"
if not errorlevel 1 (
  echo [ERROR] Port %APP_PORT% is already in use. Stop the existing service first.
  pause
  exit /b 1
)

if not exist "%LOG_DIR%" mkdir "%LOG_DIR%"

powershell -NoProfile -Command "$python=(Get-Command python).Source; $arguments=@('-m','waitress','--listen=0.0.0.0:%APP_PORT%','--threads=20','--channel-timeout=1800','app:app'); $process=Start-Process -FilePath $python -ArgumentList $arguments -WorkingDirectory '%~dp0' -WindowStyle Hidden -RedirectStandardOutput '%STDOUT_LOG%' -RedirectStandardError '%STDERR_LOG%' -PassThru; Set-Content -LiteralPath '%PID_FILE%' -Value $process.Id -Encoding ascii"

if not exist "%PID_FILE%" (
  echo [ERROR] Failed to start Waitress. Check: %STDERR_LOG%
  pause
  exit /b 1
)

set /p NEW_PID=<"%PID_FILE%"
timeout /t 2 /nobreak >nul

powershell -NoProfile -Command "if (Get-Process -Id %NEW_PID% -ErrorAction SilentlyContinue) { exit 0 } else { exit 1 }"
if errorlevel 1 (
  del /q "%PID_FILE%" >nul 2>nul
  echo [ERROR] Waitress exited during startup. Check: %STDERR_LOG%
  pause
  exit /b 1
)

echo [OK] YCC-Edit started in the background.
echo URL: http://127.0.0.1:%APP_PORT%
echo PID: %NEW_PID%
echo Logs: %LOG_DIR%
exit /b 0
