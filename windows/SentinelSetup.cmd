@echo off
setlocal
cd /d "%~dp0"
title LIN4CRE SENTINEL Setup
set "SENTINEL_PYTHON="
for /f "delims=" %%i in ('powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0Find-Python.ps1"') do if not defined SENTINEL_PYTHON set "SENTINEL_PYTHON=%%i"
if defined SENTINEL_PYTHON (
  start "LIN4CRE SENTINEL" "%SENTINEL_PYTHON%" "%~dp0SentinelSetup.pyw"
  exit /b 0
)
powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -STA -File "%~dp0Bootstrap.ps1"
if errorlevel 1 pause
endlocal
