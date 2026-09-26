"""Inspeciona um backup SQLite existente, sem restaurar ou imprimir registros."""
import argparse
import sqlite3
from contextlib import closing
from pathlib import Path


def verificar(path):
    path = Path(path).resolve(strict=True)
    with path.open('rb') as stream:
        if stream.read(16) != b'SQLite format 3\x00':
            raise ValueError('Formato inválido.')
    with closing(sqlite3.connect(path.as_uri() + '?mode=ro', uri=True)) as database:
        database.execute('PRAGMA query_only=ON')
        if database.execute('PRAGMA integrity_check').fetchall() != [('ok',)]:
            raise ValueError('Integridade inválida.')
        if database.execute('PRAGMA foreign_key_check').fetchone() is not None:
            raise ValueError('Referências inválidas.')
        tables = {row[0] for row in database.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        required = {'django_migrations', 'auth_user', 'rastreamento_pessoa',
                    'rastreamento_dispositivo', 'rastreamento_localizacao',
                    'rastreamento_linkdispositivo'}
        if not required.issubset(tables):
            raise ValueError('Estrutura incompleta.')


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('arquivo', help='Caminho do backup privado existente.')
    args = parser.parse_args(argv)
    try:
        verificar(args.arquivo)
    except (OSError, ValueError, sqlite3.Error):
        print('Backup não aprovado: confira acesso, formato, integridade, referências e tabelas. Nenhum registro foi exibido.')
        return 1
    print('Integridade, referências e tabelas básicas aprovadas. Ainda é necessário ensaiar a restauração isolada da aplicação.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
