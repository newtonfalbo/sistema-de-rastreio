$ErrorActionPreference = 'Stop'
$rastreioRaiz = Split-Path -Parent $PSScriptRoot
foreach ($rastreioTipo in @('tunnel', 'mobile')) {
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
    if ($rastreioProcesso.ExecutablePath -ne $rastreioEsperado -or -not $rastreioProcesso.CommandLine -or -not $rastreioProcesso.CommandLine.Contains($rastreioArgumento)) {
        throw "O PID salvo de $rastreioTipo pertence a outro processo. Nenhum encerramento foi realizado para ele."
    }
    if ($rastreioTipo -eq 'mobile') {
        # O launcher do venv no Windows cria um Python filho que atende a porta.
        $rastreioFilhos = @(Get-CimInstance Win32_Process -Filter "ParentProcessId = $rastreioProcessId" | Where-Object { $_.Name -eq 'python.exe' })
        foreach ($rastreioFilho in $rastreioFilhos) {
            if (-not $rastreioFilho.CommandLine -or -not $rastreioFilho.CommandLine.Contains($rastreioArgumento) -or $rastreioFilho.CreationDate -lt $rastreioProcesso.CreationDate) {
                throw 'Processo filho inesperado. Confira a arvore de processos antes de encerrar o receptor.'
            }
        }
        foreach ($rastreioFilho in $rastreioFilhos) {
            $rastreioFilhoAtual = Get-CimInstance Win32_Process -Filter "ProcessId = $($rastreioFilho.ProcessId)"
            if ($rastreioFilhoAtual) {
                if ($rastreioFilhoAtual.CreationDate -ne $rastreioFilho.CreationDate -or $rastreioFilhoAtual.ParentProcessId -ne $rastreioProcessId) { throw 'O processo filho mudou. Encerramento interrompido.' }
                Stop-Process -Id $rastreioFilho.ProcessId -ErrorAction Stop
            }
        }
    }
    # O launcher pode terminar sozinho quando seu filho encerra.
    $rastreioAtual = Get-CimInstance Win32_Process -Filter "ProcessId = $rastreioProcessId"
    if ($rastreioAtual) {
        if ($rastreioAtual.CreationDate -ne $rastreioProcesso.CreationDate) { throw 'O PID foi reutilizado. Encerramento interrompido.' }
        Stop-Process -Id $rastreioProcessId -ErrorAction Stop
    }
    Write-Host "$rastreioTipo encerrado."
}
if (Get-NetTCPConnection -LocalAddress '127.0.0.1' -LocalPort 8001 -State Listen -ErrorAction SilentlyContinue) {
    throw 'A porta do receptor continua ocupada. Confira processos restantes; o encerramento nao foi confirmado.'
}
$rastreioOrigin = Join-Path $rastreioRaiz '.local\mobile-origin.txt'
if (Test-Path -LiteralPath $rastreioOrigin) { Set-Content -LiteralPath $rastreioOrigin -Value '' -Encoding utf8 }
Write-Host 'Teste externo encerrado. O painel local continua disponivel.'
