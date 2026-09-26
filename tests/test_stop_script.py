import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from unittest import skipUnless

from django.conf import settings
from django.test import SimpleTestCase


HARNESS = r'''
$ErrorActionPreference = 'Stop'
$global:stopped = [System.Collections.Generic.List[int]]::new()
$global:created = [datetime]'2026-01-01T00:00:00Z'
$global:parent = [pscustomobject]@{ProcessId=101; ExecutablePath=(Join-Path $env:TEST_ROOT '.venv/Scripts/python.exe'); CommandLine='python scripts/servidor-celular.py'; CreationDate=$global:created}
$global:child = [pscustomobject]@{ProcessId=102; ParentProcessId=101; Name='python.exe'; CommandLine='python scripts/servidor-celular.py'; CreationDate=$global:created.AddSeconds(1)}
if ($env:TEST_CASE -eq 'wrong_parent') { $global:parent.ExecutablePath = 'unrelated.exe' }
if ($env:TEST_CASE -eq 'wrong_child') { $global:child.CommandLine = 'python unrelated.py' }
function Get-CimInstance {
    param($ClassName, $Filter)
    if ($Filter -eq 'ProcessId = 101') { return $global:parent }
    if ($Filter -eq 'ParentProcessId = 101') { return $global:child }
    if ($Filter -eq 'ProcessId = 102') { return $global:child }
}
function Stop-Process { param([int]$Id, $ErrorAction) $global:stopped.Add($Id) }
function Get-NetTCPConnection {
    param($LocalAddress, $LocalPort, $State, $ErrorAction)
    if ($env:TEST_CASE -eq 'busy') { return [pscustomobject]@{OwningProcess=999} }
}
$failed = $false
try { & (Join-Path $env:TEST_ROOT 'scripts/parar-teste-celular.ps1') }
catch { $failed = $true }
$expectedFailure = $env:TEST_CASE -ne 'normal'
if ($failed -ne $expectedFailure) { throw 'Unexpected completion status.' }
if ($env:TEST_CASE -in @('normal','busy')) {
    if (($global:stopped -join ',') -ne '102,101') { throw 'Child must stop before parent.' }
} elseif ($global:stopped.Count -ne 0) { throw 'An unrelated process was stopped.' }
$origin = Get-Content (Join-Path $env:TEST_ROOT '.local/mobile-origin.txt') -Raw
if ($env:TEST_CASE -eq 'normal') {
    if ($origin.Trim()) { throw 'Origin was not cleared.' }
} elseif ($origin.Trim() -ne 'sentinel') { throw 'Failure was reported as success.' }
'''


@skipUnless(shutil.which('pwsh'), 'PowerShell indisponível para testar script Windows.')
class StopScriptTests(SimpleTestCase):
    def test_parada_identifica_filhos_e_recusa_processos_inesperados(self):
        for scenario in ['normal', 'wrong_parent', 'wrong_child', 'busy']:
            with self.subTest(scenario=scenario), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                (root / 'scripts').mkdir()
                (root / '.local').mkdir()
                shutil.copyfile(settings.BASE_DIR / 'scripts/parar-teste-celular.ps1', root / 'scripts/parar-teste-celular.ps1')
                (root / '.local/mobile.pid').write_text('101')
                (root / '.local/mobile-origin.txt').write_text('sentinel')
                harness = root / 'test.ps1'
                harness.write_text(HARNESS, encoding='utf-8')
                result = subprocess.run([shutil.which('pwsh'), '-NoProfile', '-File', str(harness)],
                                        env={**os.environ, 'TEST_ROOT': directory, 'TEST_CASE': scenario},
                                        capture_output=True, text=True, timeout=30)
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
