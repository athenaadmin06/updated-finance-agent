@echo off
setlocal
cd /d "%~dp0"

echo Running Angular API self-tests...
echo.
node test.mjs
echo.
pause

