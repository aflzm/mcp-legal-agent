param([int]$Port = 8001)
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$projectPython = Join-Path $projectRoot '.venv\Scripts\python.exe'
if (Test-Path -LiteralPath $projectPython) {
    $runner = $projectPython
} else {
    $runner = 'python'
}
Push-Location $projectRoot
try {
    $env:PYTHONIOENCODING = 'utf-8'
    & $runner -c 'import sys; assert sys.version_info >= (3, 10), "Python 3.10+ required"'
    if ($LASTEXITCODE -ne 0) { throw 'Python 3.10+ required' }
    & $runner -m uvicorn main:app --host 127.0.0.1 --port $Port
} finally {
    Pop-Location
}