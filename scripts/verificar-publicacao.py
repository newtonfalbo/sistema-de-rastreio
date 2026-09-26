"""Verifica o índice Git sem imprimir segredos. Execute antes de cada commit."""
import re
import subprocess
from pathlib import PurePosixPath


SECRET_PATTERNS = (
    rb'-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----',
    rb'gh[pousr]_[A-Za-z0-9]{30,}',
    rb'github_pat_[A-Za-z0-9_]{40,}',
    rb'https://[a-z0-9-]+\.trycloudflare\.com',
)


def inspect_blob(path, data):
    parts = PurePosixPath(path.lower()).parts
    name = parts[-1]
    problems = []
    if any(part in {'.local', '.venv', 'node_modules', '__pycache__'} for part in parts):
        problems.append('diretório privado ou gerado')
    if (name == '.env' or name.startswith('.env.') and name not in {'.env.example', '.env.sample'}
            or name.endswith(('.sqlite3', '.sqlite3-journal', '.sqlite3-wal', '.sqlite3-shm', '.db', '.log', '.key', '.pem'))):
        problems.append('arquivo potencialmente privado')
    if data.startswith(b'SQLite format 3\x00'):
        problems.append('banco SQLite, independentemente da extensão')
    if any(re.search(pattern, data) for pattern in SECRET_PATTERNS):
        problems.append('possível credencial ou endereço temporário')
    return problems


def check_index(root):
    entries = subprocess.check_output(['git', 'ls-files', '--stage', '-z'], cwd=root)
    problems = []
    for entry in entries.split(b'\x00'):
        if not entry:
            continue
        metadata, raw_path = entry.split(b'\t', 1)
        mode, oid, stage = metadata.split()
        path = raw_path.decode('utf-8', errors='replace')
        if stage != b'0':
            problems.append((path, ['conflito não resolvido']))
            continue
        if mode == b'160000':
            problems.append((path, ['submódulo não inspecionado']))
            continue
        data = subprocess.check_output(['git', 'cat-file', 'blob', oid.decode('ascii')], cwd=root)
        findings = inspect_blob(path, data)
        if findings:
            problems.append((path, findings))
    return problems


def main():
    try:
        problems = check_index('.')
    except subprocess.CalledProcessError:
        print('Não foi possível verificar o índice Git; publicação não validada.')
        return 2
    if problems:
        for path, reasons in problems:
            print(f'BLOQUEADO: {path!r}: {", ".join(reasons)}')
        print('Revise os arquivos antes de publicar. Conteúdo suspeito foi omitido.')
        return 1
    print('Índice Git aprovado pelas regras locais. Revise também dados pessoais e segredos não reconhecidos.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
