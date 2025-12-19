@echo off
net session >nul 2>&1 || (
    powershell -Command "Start-Process '%~f0' -Verb RunAs"
    exit /b
)

cd /d "%~dp0"

echo npm install...
call npm.cmd install || goto error

echo npm run dist...
call npm.cmd run dist || goto error

echo.
echo BUILD BASARILI
pause
exit /b 0

:error
echo.
echo BUILD HATASI!
pause
exit /b 1
