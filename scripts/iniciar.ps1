param([switch]$SemAbrir)
$ErrorActionPreference = 'Stop'
$rastreioRaiz = Split-Path -Parent $PSScriptRoot
$rastreioPython = Join-Path $rastreioRaiz '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $rastreioPython)) {
    throw 'Ambiente Python ausente. Na raiz: python -m venv .venv; depois .\.venv\Scripts\python.exe -m pip install -r requirements.lock'
}
Push-Location $rastreioRaiz
try {
    & $rastreioPython manage.py check
    if ($LASTEXITCODE -ne 0) { throw 'A verificacao do Django falhou. Confira a mensagem acima.' }
    & $rastreioPython manage.py migrate --noinput
    if ($LASTEXITCODE -ne 0) { throw 'Nao foi possivel preparar o banco.' }
    & $rastreioPython manage.py shell -c 'import sys; from django.contrib.auth import get_user_model; sys.exit(0 if get_user_model().objects.filter(is_superuser=True, is_active=True).exists() else 2)'
    if ($LASTEXITCODE -eq 2) {
        Write-Host 'Primeiro acesso: escolha seu usuario e sua senha administrativa. A senha nao aparece enquanto voce digita.'
        & $rastreioPython manage.py createsuperuser
        if ($LASTEXITCODE -ne 0) { throw 'A criacao da conta nao foi concluida.' }
    } elseif ($LASTEXITCODE -ne 0) { throw 'Nao foi possivel verificar a conta administrativa.' }
    $rastreioListener = Get-NetTCPConnection -LocalPort 8000 -State Listen -ErrorAction SilentlyContinue
    if ($rastreioListener) {
        Write-Host 'Ja existe um servidor na porta 8000. Confira http://127.0.0.1:8000/ antes de iniciar outro.'
        return
    }
    Write-Host 'Servidor local: http://127.0.0.1:8000/ . Mantenha este terminal aberto. Ctrl+C encerra o servidor.'
    if (-not $SemAbrir) { Start-Process 'http://127.0.0.1:8000/' }
    & $rastreioPython manage.py runserver 127.0.0.1:8000
    if ($LASTEXITCODE -ne 0) { throw 'O servidor encerrou. Confira o erro acima.' }
} finally { Pop-Location }
