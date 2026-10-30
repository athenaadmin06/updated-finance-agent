# Run script for Java AuthService & Application Demo
$ErrorActionPreference = "Stop"

$PSScriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$SrcDir = Join-Path $PSScriptRoot "src\main\java"
$OutDir = Join-Path $PSScriptRoot "target-classes"

# Locate javac and java binaries
$javac = "javac"
$java = "java"
if (Test-Path "C:\Program Files\Java\jdk-21\bin\javac.exe") {
    $javac = "C:\Program Files\Java\jdk-21\bin\javac.exe"
    $java = "C:\Program Files\Java\jdk-21\bin\java.exe"
}

if (-not (Test-Path $OutDir)) {
    New-Item -ItemType Directory -Path $OutDir -Force | Out-Null
}

Write-Host "Compiling Java files..." -ForegroundColor Cyan
$JavaFiles = Get-ChildItem -Path (Join-Path $SrcDir "com\finance\demo\*.java") | Select-Object -ExpandProperty FullName

& $javac -d $OutDir $JavaFiles
if ($LASTEXITCODE -ne 0) {
    Write-Error "Compilation failed."
    exit $LASTEXITCODE
}

Write-Host "Running Application..." -ForegroundColor Green
& $java -cp $OutDir com.finance.demo.Application
