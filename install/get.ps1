# Download the latest Corsu release for Windows, check its SHA-256 and start the installer.
#   irm https://raw.githubusercontent.com/Platykalt/corsu/main/install/get.ps1 | iex
$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'
$base = 'https://github.com/Platykalt/corsu/releases/latest/download'
$dir = Join-Path $env:TEMP ('corsu-' + [guid]::NewGuid().ToString('N').Substring(0, 8))
New-Item -ItemType Directory -Path $dir | Out-Null
$zip = Join-Path $dir 'corsu-windows.zip'
Write-Host 'Downloading corsu-windows.zip...'
Invoke-WebRequest "$base/corsu-windows.zip" -OutFile $zip -UseBasicParsing
$expected = ([string](Invoke-RestMethod "$base/corsu-windows.zip.sha256" -UseBasicParsing)).Trim().Split(' ')[0].ToLower()
$actual = (Get-FileHash $zip -Algorithm SHA256).Hash.ToLower()
if ($expected -ne $actual) { throw "Checksum mismatch for corsu-windows.zip; nothing was installed." }
Expand-Archive -Path $zip -DestinationPath $dir
& (Join-Path $dir 'corsu\Install for Windows.cmd') @args
