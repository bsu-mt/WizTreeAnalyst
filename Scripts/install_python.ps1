#requires -version 3
# Installs Python for the current user: winget if available, else the official
# installer downloaded from python.org. Exits 0 on success, 1 on failure.
$ErrorActionPreference = 'Stop'

# Get-Command matches the Microsoft Store stub in WindowsApps, which isn't a
# real Python — probe by running it instead.
function Test-Python {
    foreach ($cmd in 'py', 'python') {
        try {
            & $cmd -c 'import sys' 2>$null
            if ($LASTEXITCODE -eq 0) { return $true }
        } catch { }
    }
    return $false
}

if (Test-Python) { exit 0 }

if (Get-Command winget -ErrorAction SilentlyContinue) {
    Write-Host 'Installing Python via winget...'
    winget install -e --id Python.Python.3.12 --scope user `
        --accept-source-agreements --accept-package-agreements
    if ($LASTEXITCODE -eq 0) { exit 0 }
    Write-Host 'winget failed, falling back to python.org installer...'
}

# ponytail: pinned version + fixed URL; bump manually when it ages out
$ver = '3.12.7'
$arch = if ($env:PROCESSOR_ARCHITECTURE -eq 'ARM64') { 'arm64' } else { 'amd64' }
$url = "https://www.python.org/ftp/python/$ver/python-$ver-$arch.exe"
$exe = Join-Path $env:TEMP "python-$ver-$arch.exe"

Write-Host "Downloading $url ..."
try {
    [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
    Invoke-WebRequest -Uri $url -OutFile $exe -UseBasicParsing
} catch {
    Write-Host "Download failed: $_"
    exit 1
}

# InstallAllUsers=0 keeps it per-user, so no UAC prompt.
Write-Host 'Running installer (this takes a minute)...'
$p = Start-Process -FilePath $exe -Wait -PassThru -ArgumentList @(
    '/quiet', 'InstallAllUsers=0', 'PrependPath=1', 'Include_tcltk=1', 'Include_test=0'
)
Remove-Item $exe -ErrorAction SilentlyContinue

if ($p.ExitCode -ne 0) {
    Write-Host "Installer exited with $($p.ExitCode)."
    exit 1
}
exit 0
