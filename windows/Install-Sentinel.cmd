@echo off
setlocal EnableExtensions EnableDelayedExpansion
title LIN4CRE SENTINEL Setup
cd /d "%~dp0"

set "RELEASE_URL=https://github.com/LIN4CRE/LIN4CRE-SENTINEL/releases/latest/download/LIN4CRE-SENTINEL-Windows-Setup.zip"
set "CONFIG_DIR=%LOCALAPPDATA%\LIN4CRE\SENTINEL"
set "INSTALL_ROOT=%CONFIG_DIR%\app"
set "MARKER=%CONFIG_DIR%\install-path.txt"
set "ARCHIVE=%CONFIG_DIR%\LIN4CRE-SENTINEL-Windows-Setup.zip"
set "STAGE=%TEMP%\sentinel-extract"

echo.
echo   LIN4CRE SENTINEL - one-click setup
echo   ================================
echo.

REM ---------------------------------------------------------------- 1. find
set "APP="
if exist "%MARKER%" (
  for /f "usebackq delims=" %%i in ("%MARKER%") do set "RECORDED=%%i"
  if defined RECORDED if exist "!RECORDED!\windows\SentinelSetup.pyw" set "APP=!RECORDED!"
)
if not defined APP for %%d in (
  "%INSTALL_ROOT%"
  "%USERPROFILE%\LIN4CRE-SENTINEL"
  "%USERPROFILE%\SENTINEL"
  "%~dp0"
) do (
  if not defined APP if exist "%%~d\windows\SentinelSetup.pyw" if exist "%%~d\backend\main.py" set "APP=%%~d"
)

REM ------------------------------------------------------------- 2. install
if not defined APP (
  echo   Downloading the official SENTINEL release. This only happens once.
  if not exist "%CONFIG_DIR%" mkdir "%CONFIG_DIR%" >nul 2>&1
  powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -Command "try { Invoke-WebRequest -Uri '%RELEASE_URL%' -OutFile '%ARCHIVE%' -UseBasicParsing; exit 0 } catch { exit 1 }"
  if errorlevel 1 (
    echo   The download did not complete. Check the connection and try again.
    pause
    exit /b 1
  )
  echo   Extracting the release.
  if exist "%STAGE%" rmdir /s /q "%STAGE%"
  mkdir "%STAGE%" >nul 2>&1
  powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -Command "try { Expand-Archive -LiteralPath '%ARCHIVE%' -DestinationPath '%STAGE%' -Force; exit 0 } catch { exit 1 }"
  if errorlevel 1 (
    echo   The archive could not be extracted. Nothing was changed.
    pause
    exit /b 1
  )
  if not exist "%INSTALL_ROOT%" mkdir "%INSTALL_ROOT%" >nul 2>&1
  xcopy /E /I /Q /Y "%STAGE%\LIN4CRE-SENTINEL\*" "%INSTALL_ROOT%" >nul
  rmdir /s /q "%STAGE%"
  del /q "%ARCHIVE%" >nul 2>&1
  if not exist "%INSTALL_ROOT%\windows\SentinelSetup.pyw" (
    echo   The archive did not contain a usable installation. Nothing was changed.
    pause
    exit /b 1
  )
  set "APP=%INSTALL_ROOT%"
  >"%MARKER%" echo %INSTALL_ROOT%
  echo   SENTINEL installed.
  echo.
)

REM --------------------------------------------------------------- 3. python
set "PY="
if exist "%APP%\windows\Find-Python.ps1" (
  for /f "usebackq delims=" %%i in (`powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%APP%\windows\Find-Python.ps1"`) do if not defined PY set "PY=%%i"
)

REM ------------------------------------------------------- 4. launch setup
if not defined PY (
  echo   No Python interpreter was found. Opening the native bootstrap.
  powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -STA -File "%APP%\windows\Bootstrap.ps1" -AppDir "%APP%"
  exit /b 0
)

echo   Opening the SENTINEL setup assistant.
start "LIN4CRE SENTINEL" "%PY%" "%APP%\windows\SentinelSetup.pyw"
exit /b 0
