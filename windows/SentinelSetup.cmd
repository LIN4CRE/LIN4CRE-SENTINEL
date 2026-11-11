@echo off
setlocal
cd /d "%~dp0"
title LIN4CRE SENTINEL Setup
where py >nul 2>nul
if %errorlevel%==0 (
  start "LIN4CRE SENTINEL" pyw -3 "%~dp0SentinelSetup.pyw"
  exit /b 0
)
where pythonw >nul 2>nul
if %errorlevel%==0 (
  start "LIN4CRE SENTINEL" pythonw "%~dp0SentinelSetup.pyw"
  exit /b 0
)
powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -STA -File "%~dp0Bootstrap.ps1"
if errorlevel 1 pause
endlocal
