# Download the latest Corsu release for Windows, check its SHA-256 and start the installer.
#   irm https://raw.githubusercontent.com/Platykalt/corsu/main/install/get.ps1 | iex
$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'
# CORSU_DOWNLOAD_BASE: another folder of the same archives and .sha256 files (a test build, file:// works);
# the checksum is verified the same way.
$base = if ($env:CORSU_DOWNLOAD_BASE) { $env:CORSU_DOWNLOAD_BASE } else { 'https://github.com/Platykalt/corsu/releases/latest/download' }
$dir = Join-Path $env:TEMP ('corsu-' + [guid]::NewGuid().ToString('N').Substring(0, 8))
New-Item -ItemType Directory -Path $dir | Out-Null
$zip = Join-Path $dir 'corsu-windows.zip'
Write-Host 'Downloading corsu-windows.zip...'
if ($base.StartsWith('file:')) {
    # A local folder: PowerShell 7's web commands refuse file:// addresses.
    $folder = ([uri]$base).LocalPath
    Copy-Item (Join-Path $folder 'corsu-windows.zip') $zip
    $sum = Get-Content (Join-Path $folder 'corsu-windows.zip.sha256') -Raw
} else {
    Invoke-WebRequest "$base/corsu-windows.zip" -OutFile $zip -UseBasicParsing
    $sum = [string](Invoke-RestMethod "$base/corsu-windows.zip.sha256" -UseBasicParsing)
}
$expected = $sum.Trim().Split(' ')[0].ToLower()
$actual = (Get-FileHash $zip -Algorithm SHA256).Hash.ToLower()
if ($expected -ne $actual) { throw "Checksum mismatch for corsu-windows.zip; nothing was installed." }
Expand-Archive -Path $zip -DestinationPath $dir
& (Join-Path $dir 'corsu\Install for Windows.cmd') @args
