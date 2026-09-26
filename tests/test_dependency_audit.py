import importlib.util
import io
import json
import tempfile
from pathlib import Path
from unittest.mock import patch
from urllib.error import URLError

from django.conf import settings
from django.test import SimpleTestCase

spec = importlib.util.spec_from_file_location('dependency_audit', settings.BASE_DIR / 'scripts/auditar-dependencias.py')
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)


class DependencyAuditTests(SimpleTestCase):
    packages = [{'package': {'name': 'exemplo', 'ecosystem': 'PyPI'}, 'version': '1.0'}]

    def resposta(self, payload):
        return patch.object(audit, 'urlopen', return_value=io.BytesIO(json.dumps(payload).encode()))

    def test_envia_somente_pacote_e_versao_e_aceita_resposta_completa(self):
        with self.resposta({'results': [{}]}) as request:
            self.assertEqual(audit.consultar(self.packages), [])
        body = json.loads(request.call_args.args[0].data)
        self.assertEqual(body, {'queries': self.packages})

    def test_retorna_identificadores_sem_texto_externo(self):
        with self.resposta({'results': [{'vulns': [{'id': 'GHSA-teste-1234', 'details': 'ignorar'}]}]}):
            self.assertEqual(audit.consultar(self.packages), [('exemplo', '1.0', ['GHSA-teste-1234'])])

    def test_resposta_incompleta_ou_paginada_nao_e_aprovada(self):
        for payload in [{}, {'results': []}, {'results': [{'next_page_token': 'more'}]},
                        {'results': [{'vulns': None}]}, {'results': [{'vulns': [{}]}]}]:
            with self.subTest(payload=payload), self.resposta(payload), self.assertRaises(ValueError):
                audit.consultar(self.packages)

    def test_erro_de_rede_nao_e_aprovado(self):
        with patch.object(audit, 'urlopen', side_effect=URLError('offline')):
            self.assertEqual(audit.main(), 2)

    def test_lock_rejeita_urls_opcoes_e_intervalos(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'lock.txt'
            for text in ['', 'exemplo>=1.0', '--index-url https://example.invalid', 'exemplo @ https://example.invalid/pkg']:
                path.write_text(text)
                with self.subTest(text=text), self.assertRaises(ValueError):
                    audit.carregar_pacotes(path)
            path.write_text('# comentario\nexemplo==1.0\n')
            self.assertEqual(audit.carregar_pacotes(path), self.packages)
