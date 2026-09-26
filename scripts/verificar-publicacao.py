"""Verifica o índice Git sem imprimir segredos. Execute antes de cada commit."""
import re
import os
import subprocess
import sqlite3
from contextlib import closing
from pathlib import Path, PurePosixPath


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
    if any(re.search(pattern, data) or re.search(pattern, path.encode('utf-8')) for pattern in SECRET_PATTERNS):
        problems.append('possível credencial ou endereço temporário')
    return problems


def known_private_values(root):
    root = Path(root).resolve()
    data_root = Path(os.environ.get('RASTREIO_DATA_DIR', str(root))).expanduser()
    if not data_root.is_absolute():
        raise ValueError('Diretório de dados inválido.')
    values = []
    for path in [data_root / '.local' / 'django-secret.key', root / '.local' / 'mobile-origin.txt']:
        try:
            value = path.read_bytes().removeprefix(b'\xef\xbb\xbf').strip()
        except FileNotFoundError:
            continue
        if value:
            values.append(value)
    environment_key = os.environ.get('DJANGO_SECRET_KEY', '')
    if len(environment_key) >= 32:
        values.append(environment_key.encode('utf-8'))
    database_path = data_root / 'db.sqlite3'
    if database_path.exists():
        with closing(sqlite3.connect(database_path.resolve().as_uri() + '?mode=ro', uri=True)) as database:
            database.execute('PRAGMA query_only=ON')
            has_tokens = database.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='authtoken_token'").fetchone()
            if has_tokens:
                for (key,) in database.execute('SELECT key FROM authtoken_token'):
                    if not isinstance(key, str) or not key:
                        raise ValueError('Credencial local inválida.')
                    values.append(key.encode('utf-8'))
    return values


def safe_path_label(path, private_values):
    encoded = path.encode('utf-8')
    if any(re.search(pattern, encoded) for pattern in SECRET_PATTERNS) or any(value in encoded for value in private_values):
        return '[nome omitido por conter possível segredo]'
    return path


def check_index(root):
    private_values = known_private_values(root)
    entries = subprocess.check_output(['git', 'ls-files', '--stage', '-z'], cwd=root)
    problems = []
    for entry in entries.split(b'\x00'):
        if not entry:
            continue
        metadata, raw_path = entry.split(b'\t', 1)
        mode, oid, stage = metadata.split()
        path = raw_path.decode('utf-8', errors='replace')
        display_path = safe_path_label(path, private_values)
        if stage != b'0':
            problems.append((display_path, ['conflito não resolvido']))
            continue
        if mode == b'160000':
            problems.append((display_path, ['submódulo não inspecionado']))
            continue
        data = subprocess.check_output(['git', 'cat-file', 'blob', oid.decode('ascii')], cwd=root)
        findings = inspect_blob(path, data)
        if any(value in data or value in raw_path for value in private_values):
            findings.append('segredo ou endereço privado conhecido nesta instalação')
        if findings:
            problems.append((display_path, findings))
    return problems


def main():
    try:
        problems = check_index('.')
    except (subprocess.CalledProcessError, OSError, ValueError, sqlite3.Error):
        print('Não foi possível concluir a verificação; confira Git, configuração e acesso aos arquivos privados locais.')
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
