@echo off
setlocal
cd /d "%~dp0"

echo Starting React API Server on http://localhost:3000...
echo.
node server.mjs 3000
pause

