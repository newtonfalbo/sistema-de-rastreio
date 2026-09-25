$ErrorActionPreference = 'Stop'
$rastreioRaiz = Split-Path -Parent $PSScriptRoot
foreach ($rastreioTipo in @('mobile', 'tunnel')) {
    $rastreioPidFile = Join-Path $rastreioRaiz ".local\$rastreioTipo.pid"
    if (-not (Test-Path -LiteralPath $rastreioPidFile)) { continue }
    $rastreioProcessId = 0
    if (-not [int]::TryParse((Get-Content -LiteralPath $rastreioPidFile -Raw).Trim(), [ref]$rastreioProcessId)) { throw 'Identificador de processo invalido.' }
    $rastreioProcesso = Get-CimInstance Win32_Process -Filter "ProcessId = $rastreioProcessId"
    if (-not $rastreioProcesso) { Write-Host "$rastreioTipo ja estava encerrado."; continue }
    if ($rastreioTipo -eq 'tunnel') {
        $rastreioEsperado = Join-Path $rastreioRaiz '.local\tools\cloudflared.exe'
        $rastreioArgumento = 'http://127.0.0.1:8001'
    } else {
        $rastreioEsperado = Join-Path $rastreioRaiz '.venv\Scripts\python.exe'
        $rastreioArgumento = 'scripts/servidor-celular.py'
    }
    if ($rastreioProcesso.ExecutablePath -ne $rastreioEsperado -or -not $rastreioProcesso.CommandLine.Contains($rastreioArgumento)) {
        throw "O PID salvo de $rastreioTipo pertence a outro processo. Nenhum encerramento foi realizado para ele."
    }
    Stop-Process -Id $rastreioProcessId -ErrorAction Stop
    Write-Host "$rastreioTipo encerrado."
}
$rastreioOrigin = Join-Path $rastreioRaiz '.local\mobile-origin.txt'
if (Test-Path -LiteralPath $rastreioOrigin) { Set-Content -LiteralPath $rastreioOrigin -Value '' -Encoding utf8 }
Write-Host 'Teste externo encerrado. O painel local continua disponivel.'
