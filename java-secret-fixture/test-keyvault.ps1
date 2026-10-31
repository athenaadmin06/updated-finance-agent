# Script to test fetching secrets from Azure Key Vault via Java
$ErrorActionPreference = "Stop"

$PSScriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$SrcDir = Join-Path $PSScriptRoot "src\main\java"
$OutDir = Join-Path $PSScriptRoot "target-classes"

$javac = "javac"
$java = "java"
if (Test-Path "C:\Program Files\Java\jdk-21\bin\javac.exe") {
    $javac = "C:\Program Files\Java\jdk-21\bin\javac.exe"
    $java = "C:\Program Files\Java\jdk-21\bin\java.exe"
}

if (-not (Test-Path $OutDir)) {
    New-Item -ItemType Directory -Path $OutDir -Force | Out-Null
}

Write-Host "Compiling AzureKeyVaultFetcher..." -ForegroundColor Cyan
$file = Join-Path $SrcDir "com\finance\demo\AzureKeyVaultFetcher.java"
& $javac -d $OutDir $file

Write-Host "Running AzureKeyVaultFetcher..." -ForegroundColor Green
$secretToFetch = if ($args.Count -gt 0) { $args[0] } else { "code-scan-api-key" }
& $java -cp $OutDir com.finance.demo.AzureKeyVaultFetcher $secretToFetch

