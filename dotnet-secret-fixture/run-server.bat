@echo off
setlocal
cd /d "%~dp0"

echo Starting .NET Finance API on http://localhost:5000...
echo.
dotnet run --project FinanceApi.csproj --urls "http://localhost:5000"
pause

