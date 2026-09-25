$ErrorActionPreference = 'Stop'
$rastreioRaiz = Split-Path -Parent $PSScriptRoot
$rastreioPython = Join-Path $rastreioRaiz '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $rastreioPython)) { throw 'Prepare o ambiente .venv conforme o README.' }
Push-Location $rastreioRaiz
try {
    & $rastreioPython manage.py migrate --noinput
    if ($LASTEXITCODE -ne 0) { throw 'Falha ao preparar o banco.' }
    & $rastreioPython manage.py createsuperuser
    if ($LASTEXITCODE -ne 0) { throw 'A criacao da conta nao foi concluida.' }
} finally { Pop-Location }
