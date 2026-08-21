#requires -version 3
# Prints the path to a working Python 3 with Tkinter, or nothing if none found.
# Get-Command / "where python" match the Microsoft Store stub in WindowsApps,
# which only prints an ad for the Store — so probe by actually running it.
$ErrorActionPreference = 'SilentlyContinue'

function Get-WorkingPython($exe, $prefix) {
    $out = & $exe @prefix -c 'import sys, tkinter; sys.stdout.write(sys.executable)' 2>$null
    if ($LASTEXITCODE -eq 0 -and $out) { return $out.Trim() }
    return $null
}

foreach ($c in @(
    @{ exe = 'py';     prefix = @('-3') },
    @{ exe = 'python'; prefix = @() }
)) {
    $p = Get-WorkingPython $c.exe $c.prefix
    if ($p) { Write-Output $p; exit 0 }
}

# PATH may not have refreshed after a fresh per-user install.
$fallback = Get-ChildItem "$env:LOCALAPPDATA\Programs\Python\Python3*\python.exe" |
    Sort-Object FullName -Descending | Select-Object -First 1
if ($fallback) {
    $p = Get-WorkingPython $fallback.FullName @()
    if ($p) { Write-Output $p; exit 0 }
}

exit 1
