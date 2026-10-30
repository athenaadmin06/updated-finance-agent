@echo off
setlocal
cd /d "%~dp0"

echo Running .NET self-tests...
echo.
dotnet run --project FinanceApi.csproj -- --test
echo.
pause

