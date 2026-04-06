param(
    [string]$Version = "latest",
    [string]$InstallDir = "$env:USERPROFILE\.shuoha\bin",
    [string]$Repo = $(if ($env:SHUOHA_REPO) { $env:SHUOHA_REPO } else { "synctoai/shuoha" })
)

$ErrorActionPreference = "Stop"

function Get-AssetName {
    switch ($env:PROCESSOR_ARCHITECTURE) {
        "AMD64" { return "shuoha-windows-amd64.zip" }
        "ARM64" { return "shuoha-windows-amd64.zip" }
        default { throw "当前安装脚本只支持 Windows x64。检测到架构: $env:PROCESSOR_ARCHITECTURE" }
    }
}

function Get-ReleaseUrl([string]$AssetName) {
    if ($Version -eq "latest") {
        return "https://github.com/$Repo/releases/latest/download/$AssetName"
    }

    return "https://github.com/$Repo/releases/download/$Version/$AssetName"
}

$assetName = Get-AssetName
$url = Get-ReleaseUrl -AssetName $assetName
$tempDir = Join-Path ([System.IO.Path]::GetTempPath()) ("shuoha-install-" + [guid]::NewGuid())
$archivePath = Join-Path $tempDir $assetName
$targetPath = Join-Path $InstallDir "shuoha.exe"

New-Item -ItemType Directory -Force -Path $tempDir | Out-Null
New-Item -ItemType Directory -Force -Path $InstallDir | Out-Null

try {
    Write-Host "正在下载 $url"
    Invoke-WebRequest -Uri $url -OutFile $archivePath
    Expand-Archive -Path $archivePath -DestinationPath $tempDir -Force
    Copy-Item -Path (Join-Path $tempDir "shuoha.exe") -Destination $targetPath -Force

    $normalizedInstallDir = [System.IO.Path]::GetFullPath($InstallDir).TrimEnd('\')
    $currentUserPath = [Environment]::GetEnvironmentVariable("Path", "User")
    $pathSegments = @()

    if ($currentUserPath) {
        $pathSegments = $currentUserPath.Split(';') | Where-Object { $_ -and $_.Trim() -ne "" }
    }

    $alreadyPresent = $false
    foreach ($segment in $pathSegments) {
        if ($segment.TrimEnd('\') -ieq $normalizedInstallDir) {
            $alreadyPresent = $true
            break
        }
    }

    if (-not $alreadyPresent) {
        $newUserPath = if ($currentUserPath) {
            "$currentUserPath;$normalizedInstallDir"
        } else {
            $normalizedInstallDir
        }
        [Environment]::SetEnvironmentVariable("Path", $newUserPath, "User")
    }

    $env:Path = "$normalizedInstallDir;$env:Path"
    & $targetPath --help *> $null

    Write-Host "已安装到 $targetPath"
    Write-Host "如当前终端还找不到 shuoha，请重新打开 PowerShell 或 CMD。"
    Write-Host "然后运行:"
    Write-Host "  shuoha analyze 600519"
}
finally {
    Remove-Item -Recurse -Force $tempDir -ErrorAction SilentlyContinue
}
