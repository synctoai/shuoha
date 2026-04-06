param(
    [string]$InstallDir = "$env:USERPROFILE\.shuoha\bin"
)

$ErrorActionPreference = "Stop"
$targetPath = Join-Path $InstallDir "shuoha.exe"

if (Test-Path $targetPath) {
    Remove-Item -Force $targetPath
}

$normalizedInstallDir = [System.IO.Path]::GetFullPath($InstallDir).TrimEnd('\')
$currentUserPath = [Environment]::GetEnvironmentVariable("Path", "User")

if ($currentUserPath) {
    $newSegments = $currentUserPath.Split(';') | Where-Object {
        $_ -and $_.Trim() -ne "" -and $_.TrimEnd('\') -ine $normalizedInstallDir
    }
    [Environment]::SetEnvironmentVariable("Path", ($newSegments -join ';'), "User")
}

if (Test-Path $InstallDir) {
    $remaining = Get-ChildItem -Force $InstallDir
    if ($remaining.Count -eq 0) {
        Remove-Item -Force $InstallDir
    }
}

Write-Host "已卸载 shuoha。"
Write-Host "如当前终端仍然能访问旧 PATH，请重新打开 PowerShell 或 CMD。"
