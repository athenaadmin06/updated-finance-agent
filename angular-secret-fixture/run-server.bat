@echo off
setlocal
cd /d "%~dp0"

echo Starting Angular API Server on http://localhost:4200...
echo.
node server.mjs 4200
pause

