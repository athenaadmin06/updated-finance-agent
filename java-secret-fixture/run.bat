@echo off
setlocal
cd /d "%~dp0"

set "JAVAC_BIN=javac"
set "JAVA_BIN=java"
if exist "C:\Program Files\Java\jdk-21\bin\javac.exe" (
    set "JAVAC_BIN=C:\Program Files\Java\jdk-21\bin\javac.exe"
    set "JAVA_BIN=C:\Program Files\Java\jdk-21\bin\java.exe"
)

if not exist target-classes mkdir target-classes

echo Compiling Java files...
"%JAVAC_BIN%" -d target-classes src\main\java\com\finance\demo\*.java
if %ERRORLEVEL% neq 0 (
    echo Compilation failed.
    pause
    exit /b %ERRORLEVEL%
)

echo Running Application...
echo.
"%JAVA_BIN%" -cp target-classes com.finance.demo.Application
echo.
pause
