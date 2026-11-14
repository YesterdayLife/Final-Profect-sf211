$python = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $python)) {
    Write-Error "Missing .venv. Create it with Python 3.13, then run: pip install -r requirements.txt"
    exit 1
}

& $python (Join-Path $PSScriptRoot "main.py")
exit $LASTEXITCODE
