"""Consulta OSV usando apenas nomes e versões do requirements.lock público."""
import json
import re
from pathlib import Path
from urllib.error import URLError
from urllib.request import Request, urlopen


def carregar_pacotes(path):
    packages = []
    for line in Path(path).read_text(encoding='utf-8-sig').splitlines():
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        match = re.fullmatch(r'([A-Za-z0-9][A-Za-z0-9_.-]*)==([A-Za-z0-9][A-Za-z0-9_.+!-]*)', line)
        if not match:
            raise ValueError('O arquivo deve conter somente versões exatas, sem URLs ou opções.')
        packages.append({'package': {'name': match[1], 'ecosystem': 'PyPI'}, 'version': match[2]})
    if not packages:
        raise ValueError('Nenhum pacote encontrado.')
    return packages


def consultar(packages):
    request = Request('https://api.osv.dev/v1/querybatch',
                      data=json.dumps({'queries': packages}).encode('utf-8'),
                      headers={'Content-Type': 'application/json', 'User-Agent': 'Rastreio-dependency-audit'},
                      method='POST')
    with urlopen(request, timeout=30) as response:
        payload = json.load(response)
    results = payload.get('results') if isinstance(payload, dict) else None
    if not isinstance(results, list) or len(results) != len(packages):
        raise ValueError('Resposta incompleta.')
    findings = []
    for package, result in zip(packages, results):
        if not isinstance(result, dict) or result.get('next_page_token'):
            raise ValueError('Resposta incompleta ou paginada; requer revisão.')
        vulns = result.get('vulns', [])
        if not isinstance(vulns, list):
            raise ValueError('Formato de avisos inválido.')
        ids = []
        for vuln in vulns:
            identifier = vuln.get('id') if isinstance(vuln, dict) else None
            if not isinstance(identifier, str) or not re.fullmatch(r'[A-Za-z0-9_.-]{1,150}', identifier):
                raise ValueError('Identificador de aviso inválido.')
            ids.append(identifier)
        if ids:
            findings.append((package['package']['name'], package['version'], sorted(set(ids))))
    return findings


def main():
    try:
        packages = carregar_pacotes(Path(__file__).resolve().parent.parent / 'requirements.lock')
        findings = consultar(packages)
    except (OSError, URLError, ValueError):
        print('Auditoria inconclusiva: confira o lock, a rede e o serviço OSV. Não é aprovação de segurança.')
        return 2
    for name, version, ids in findings:
        print(f'REVISAR: {name}=={version}: {", ".join(ids)}')
    if findings:
        print('Avisos podem ser aliases do mesmo problema; revise aplicabilidade e correção antes de publicar.')
        return 1
    print(f'OSV: nenhum aviso retornado para {len(packages)} pacotes nesta consulta. Não cobre falhas desconhecidas.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
