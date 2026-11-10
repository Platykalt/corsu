# Download the latest Corsu release for Windows, check its SHA-256 and start the installer.
# Running it again updates (or repairs) the installed Corsu: parts and choices are kept, parts switched off stay off.
#   irm https://raw.githubusercontent.com/Platykalt/corsu/main/install/get.ps1 | iex
$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'
# Windows PowerShell 5.1 may still offer only TLS 1.0, which GitHub refuses: allow TLS 1.2 as well.
[Net.ServicePointManager]::SecurityProtocol = [Net.ServicePointManager]::SecurityProtocol -bor [Net.SecurityProtocolType]::Tls12
# CORSU_DOWNLOAD_BASE: a development override pointing at another folder of the same archives and .sha256 files
# (a test build, file:// works). SHA-256 only proves the download matches the .sha256 fetched from the SAME base,
# i.e. the transfer was not corrupted; it does not prove where the files come from. The authenticity of the
# official release rests on HTTPS to github.com, not on the checksum. A non-default base is announced below.
$base = if ($env:CORSU_DOWNLOAD_BASE) { $env:CORSU_DOWNLOAD_BASE } else { 'https://github.com/Platykalt/corsu/releases/latest/download' }
if ($env:CORSU_DOWNLOAD_BASE) {
    Write-Warning "Downloading from CORSU_DOWNLOAD_BASE=$base, not the official releases (SHA-256 checks the transfer, not the source)."
}
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
    # A file, not Invoke-RestMethod: the .sha256 comes as application/octet-stream, which PowerShell versions read
    # differently (text or bytes).
    Invoke-WebRequest "$base/corsu-windows.zip.sha256" -OutFile "$zip.sha256" -UseBasicParsing
    $sum = Get-Content "$zip.sha256" -Raw
}
$expected = $sum.Trim().Split(' ')[0].ToLower()
$actual = (Get-FileHash $zip -Algorithm SHA256).Hash.ToLower()
if ($expected -ne $actual) { throw "Checksum mismatch for corsu-windows.zip; nothing was installed." }
Expand-Archive -Path $zip -DestinationPath $dir
& (Join-Path $dir 'corsu\Install for Windows.cmd') @args
