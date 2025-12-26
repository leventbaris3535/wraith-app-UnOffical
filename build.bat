@echo off
chcp 65001 >nul
title WraithApp Builder

 net session >nul 2>&1 || (
     powershell -Command "Start-Process '%~f0' -Verb RunAs"
     exit /b
 )

cd /d "%~dp0"

echo [1/3] Cleaning previous build...
if exist dist rmdir /s /q dist

echo [2/3] Installing dependencies...
call npm.cmd install
if %ERRORLEVEL% neq 0 goto error

echo [3/3] Building application...
call npm.cmd run dist
if %ERRORLEVEL% neq 0 goto error

echo.
echo ========================================
echo   BUILD SUCCESSFUL
echo ========================================
echo.
echo Generated files in 'dist' folder:
dir /b dist\*.exe
echo.
pause
exit /b 0

:error
echo.
echo ========================================
echo   BUILD FAILED
echo ========================================
echo.
pause
exit /b 1
