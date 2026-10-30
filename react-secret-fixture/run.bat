@echo off
setlocal
cd /d "%~dp0"

echo Running React API self-tests...
echo.
node test.mjs
echo.
pause

