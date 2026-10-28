# VLC and Notepad++ for the Windows programs check (CI runner). Chocolatey's feed sometimes answers 503 for one
# package: try it three times, then take VLC from VideoLAN with its SHA-256 checked. Stops with an explicit message
# when VLC is still missing. The parameters are for testing this fallback (ci.yml, job vlc-fallback):
#   -ChocoSource  a Chocolatey source to use instead of the default one (a bogus one makes Chocolatey fail)
#   -ChocoTries   how many times Chocolatey is tried (default 3)
#   -Base         where VideoLAN's Windows installers are listed (default: the latest release)
#   -Tamper       change one byte of the downloaded installer before its checksum is checked (must be refused)
param(
    [string]$ChocoSource = '',
    [int]$ChocoTries = 3,
    [string]$Base = 'https://download.videolan.org/pub/videolan/vlc/last/win64/',
    [switch]$Tamper
)
$ErrorActionPreference = 'Stop'
# Chocolatey's exit code is read below; it must not stop the script by itself.
$PSNativeCommandUseErrorActionPreference = $false
$vlc = 'C:\Program Files\VideoLAN\VLC\vlc.exe'
$notepad = 'C:\Program Files\Notepad++\notepad++.exe'

$source = @()
if ($ChocoSource) { $source = @("--source=$ChocoSource") }
foreach ($try in 1..$ChocoTries) {
    choco install vlc notepadplusplus -y --no-progress $source
    Write-Host "Chocolatey try ${try}: exit code $LASTEXITCODE"
    if ((Test-Path $vlc) -and (Test-Path $notepad)) { break }
    if ($try -lt $ChocoTries) { Start-Sleep -Seconds 30 }
}

if (-not (Test-Path $vlc)) {
    Write-Host "VLC missing after Chocolatey: downloading it from $Base"
    try {
        $listing = Invoke-WebRequest $Base -UseBasicParsing -TimeoutSec 60
    } catch {
        throw "VLC download: $Base cannot be reached ($($_.Exception.Message))"
    }
    $name = $listing.Links.href | Where-Object { $_ -match '^vlc-[0-9.]+-win64\.exe$' } | Select-Object -First 1
    if (-not $name) { throw "VLC download: no vlc-<version>-win64.exe listed at $Base" }
    $file = Join-Path $env:RUNNER_TEMP $name
    try {
        Invoke-WebRequest "$Base$name" -OutFile $file -UseBasicParsing -TimeoutSec 600
        Invoke-WebRequest "$Base$name.sha256" -OutFile "$file.sha256" -UseBasicParsing -TimeoutSec 60
    } catch {
        throw "VLC download: $Base$name or its .sha256 could not be fetched ($($_.Exception.Message))"
    }
    # VideoLAN's .sha256 file: "<hash>  <file name>".
    $expected = ((Get-Content "$file.sha256" -Raw).Trim() -split '\s+')[0]
    if ($expected -notmatch '^[0-9a-fA-F]{64}$') { throw "VLC download: no SHA-256 in $Base$name.sha256" }
    if ($Tamper) {
        $bytes = [IO.File]::ReadAllBytes($file)
        $bytes[1000] = $bytes[1000] -bxor 0xFF
        [IO.File]::WriteAllBytes($file, $bytes)
        Write-Host "Tampered: one byte of $name changed before the checksum"
    }
    $actual = (Get-FileHash $file -Algorithm SHA256).Hash
    Write-Host "SHA-256 expected $expected"
    Write-Host "SHA-256 actual   $actual"
    if ($actual -ne $expected) { Remove-Item $file; throw "VLC download: checksum mismatch for $name" }
    Start-Process $file -ArgumentList '/S' -Wait
}
if (-not (Test-Path $vlc)) { throw 'VLC could not be installed (Chocolatey and VideoLAN)' }
Write-Host "VLC installed: $vlc, version $((Get-Item $vlc).VersionInfo.ProductVersion)"
