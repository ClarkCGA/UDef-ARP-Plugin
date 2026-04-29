param(
    [string]$QgisPythonPath = "",
    [string]$RequirementsPath = "requirements/windows-qgis.txt"
)

$ErrorActionPreference = "Stop"

function Resolve-QgisPython {
    param([string]$PathHint)

    if ($PathHint -and (Test-Path $PathHint)) {
        return (Resolve-Path $PathHint).Path
    }

    $candidates = Get-ChildItem "C:\Program Files" -Filter "QGIS*" -Directory -ErrorAction SilentlyContinue |
        Sort-Object Name -Descending |
        ForEach-Object { Join-Path $_.FullName "bin\python-qgis.bat" } |
        Where-Object { Test-Path $_ }

    if ($candidates.Count -gt 0) {
        return $candidates[0]
    }

    throw "Could not find python-qgis.bat. Re-run with -QgisPythonPath <full path>."
}

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$requirementsFullPath = Join-Path $repoRoot $RequirementsPath
if (-not (Test-Path $requirementsFullPath)) {
    throw "Requirements file not found: $requirementsFullPath"
}

$qgisPython = Resolve-QgisPython -PathHint $QgisPythonPath
Write-Host "Using QGIS Python launcher: $qgisPython"
Write-Host "Requirements file: $requirementsFullPath"

& $qgisPython -m pip install --upgrade pip setuptools wheel
& $qgisPython -m pip install -r $requirementsFullPath
& $qgisPython (Join-Path $repoRoot "scripts\verify_qgis_deps.py")

Write-Host "Dependency installation and verification completed."
