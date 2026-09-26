"""Diagnóstico sem credenciais, posições ou exibição do endereço privado."""
import argparse
import sys
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, ProxyHandler, Request, build_opener

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from config.mobile_origin import load_mobile_origin


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def read_origin(root):
    value = load_mobile_origin(root)
    parsed = urlsplit(value)
    return value, parsed.netloc


def probe(opener, url, host=None):
    headers = {'User-Agent': 'Sistema-de-Rastreio-Diagnostico/1.0'}
    if host:
        headers['Host'] = host
    request = Request(url, headers=headers)
    try:
        response = opener.open(request, timeout=10)
    except HTTPError as error:
        response = error
    with response:
        return response.code, response.headers


def main(argv=None, *, root=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--externo', action='store_true', help='Também consultar o HTTPS configurado.')
    args = parser.parse_args(argv)
    try:
        origin, host = read_origin(root or Path(__file__).resolve().parent.parent)
    except (OSError, UnicodeError, ValueError):
        print('INCONCLUSIVO: configuração privada ausente, inacessível ou inválida.')
        return 2
    # Loopback nunca deve ser encaminhado a um proxy do ambiente.
    local = build_opener(ProxyHandler({}), NoRedirect())
    remote = build_opener(NoRedirect())
    checks = [('Receptor local', local, 'http://127.0.0.1:8001/celular/', host, 200)]
    if args.externo:
        checks += [('Página HTTPS', remote, origin + '/celular/', None, 200)]
        checks += [(label, remote, origin + path, None, 404) for label, path in (
            ('Raiz externa isolada', '/'), ('Admin externo isolado', '/admin/'),
            ('API externa isolada', '/api/pessoas/'))]
    success = True
    for label, opener, url, request_host, expected in checks:
        try:
            code, headers = probe(opener, url, request_host)
            safe_headers = ('no-store' in headers.get('Cache-Control', '').lower()
                            and headers.get('Referrer-Policy') == 'no-referrer')
            passed = code == expected and safe_headers
            print(f'{label}: {"OK" if passed else "FALHOU"} (HTTP {code}; cabeçalhos {"OK" if safe_headers else "inesperados"}).')
        except (URLError, OSError, ValueError):
            passed = False
            print(f'{label}: FALHOU (conexão, TLS ou resposta indisponível).')
        success &= passed
    if not args.externo:
        print('HTTPS externo não verificado. Use --externo para testar o acesso remoto.')
    print('Este diagnóstico não valida GPS, permissões do celular ou envio de posição.')
    return 0 if success else 1


if __name__ == '__main__':
    raise SystemExit(main())
