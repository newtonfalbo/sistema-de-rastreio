from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.core.cache import cache
from django.db import IntegrityError, transaction
from django.test import TestCase
from django.utils import timezone
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient, APITestCase

from rastreamento.models import Dispositivo, Localizacao, Pessoa


class RastreioAPITests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.usuario = get_user_model().objects.create_user(username='ana', password='Senha-de-teste-927!')
        cls.outro = get_user_model().objects.create_user(username='bruno', password='Senha-de-teste-928!')
        cls.pessoa = Pessoa.objects.create(responsavel=cls.usuario, nome='Pessoa A', compartilhamento_ativo=True)
        cls.alheia = Pessoa.objects.create(responsavel=cls.outro, nome='Pessoa B', compartilhamento_ativo=True)
        cls.dispositivo = Dispositivo.objects.create(pessoa=cls.pessoa, nome='Celular A')
        cls.alheio = Dispositivo.objects.create(pessoa=cls.alheia, nome='Celular B')

    def setUp(self):
        cache.clear()
        self.client.force_authenticate(self.usuario)

    def payload(self, **overrides):
        data = {'dispositivo': str(self.dispositivo.pk), 'latitude': '-3.7319000',
                'longitude': '-38.5267000', 'precisao_metros': 12.0,
                'capturado_em': timezone.now().isoformat()}
        data.update(overrides)
        return data

    def registrar(self, **overrides):
        return self.client.post('/api/localizacoes/', self.payload(**overrides), format='json')

    def test_sem_autenticacao_nao_acessa_api(self):
        self.client.force_authenticate(None)
        for url in ['/api/', '/api/pessoas/', '/api/dispositivos/', '/api/localizacoes/']:
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, 401)
        self.assertEqual(self.registrar().status_code, 401)

    def test_token_real_e_token_invalido(self):
        self.client.force_authenticate(None)
        token = Token.objects.create(user=self.usuario)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')
        self.assertEqual(self.client.get('/api/pessoas/').status_code, 200)
        self.client.credentials(HTTP_AUTHORIZATION='Token invalido')
        self.assertEqual(self.client.get('/api/pessoas/').status_code, 401)

    def test_usuario_inativo_nao_autentica(self):
        token = Token.objects.create(user=self.usuario)
        self.usuario.is_active = False
        self.usuario.save()
        self.client.force_authenticate(None)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')
        self.assertEqual(self.client.get('/api/pessoas/').status_code, 401)

    def test_sessao_exige_csrf_na_escrita(self):
        client = APIClient(enforce_csrf_checks=True)
        client.force_login(self.usuario)
        self.assertEqual(client.get('/api/pessoas/').status_code, 200)
        self.assertEqual(client.post('/api/pessoas/', {'nome': 'Teste'}, format='json').status_code, 403)

    def test_cadastro_define_responsavel_e_compartilhamento_desativado(self):
        response = self.client.post('/api/pessoas/', {'nome': 'Nova pessoa', 'responsavel': self.outro.pk}, format='json')
        self.assertEqual(response.status_code, 201)
        pessoa = Pessoa.objects.get(pk=response.data['id'])
        self.assertEqual(pessoa.responsavel, self.usuario)
        self.assertFalse(pessoa.compartilhamento_ativo)

    def test_fluxo_completo_pessoa_dispositivo_localizacao(self):
        pessoa = self.client.post('/api/pessoas/', {'nome': 'Teste', 'compartilhamento_ativo': True}, format='json')
        self.assertEqual(pessoa.status_code, 201)
        dispositivo = self.client.post('/api/dispositivos/', {'nome': 'GPS', 'pessoa': pessoa.data['id']}, format='json')
        self.assertEqual(dispositivo.status_code, 201)
        localizacao = self.registrar(dispositivo=dispositivo.data['id'])
        self.assertEqual(localizacao.status_code, 201)
        latest = self.client.get(f"/api/pessoas/{pessoa.data['id']}/ultima-localizacao/")
        self.assertEqual(latest.data['id'], localizacao.data['id'])

    def test_listas_isoladas_por_responsavel(self):
        self.assertEqual(self.client.get('/api/pessoas/').data['count'], 1)
        self.assertEqual(self.client.get('/api/dispositivos/').data['count'], 1)
        self.assertEqual(self.registrar().status_code, 201)
        self.client.force_authenticate(self.outro)
        self.assertEqual(self.client.get('/api/localizacoes/').data['count'], 0)

    def test_nao_acessa_modifica_ou_exclui_objetos_alheios(self):
        for recurso, objeto in [('pessoas', self.alheia), ('dispositivos', self.alheio)]:
            url = f'/api/{recurso}/{objeto.pk}/'
            self.assertEqual(self.client.get(url).status_code, 404)
            self.assertEqual(self.client.patch(url, {'nome': 'Alterado'}, format='json').status_code, 404)
            self.assertEqual(self.client.delete(url).status_code, 404)
        self.assertEqual(self.client.get(f'/api/pessoas/{self.alheia.pk}/ultima-localizacao/').status_code, 404)

    def test_relacoes_alheias_rejeitadas(self):
        response = self.client.post('/api/dispositivos/', {'pessoa': str(self.alheia.pk), 'nome': 'Invasor'}, format='json')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(self.registrar(dispositivo=str(self.alheio.pk)).status_code, 400)

    def test_localizacao_alheia_retorna_404(self):
        criada = self.registrar()
        self.client.force_authenticate(self.outro)
        self.assertEqual(self.client.get(f"/api/localizacoes/{criada.data['id']}/").status_code, 404)
        response = self.client.get('/api/localizacoes/', {'pessoa': str(self.pessoa.pk)})
        self.assertEqual(response.data['count'], 0)

    def test_dispositivo_nao_pode_mudar_de_pessoa(self):
        outra = Pessoa.objects.create(responsavel=self.usuario, nome='Outra pessoa')
        response = self.client.patch(f'/api/dispositivos/{self.dispositivo.pk}/', {'pessoa': str(outra.pk)}, format='json')
        self.assertEqual(response.status_code, 400)

    def test_coordenadas_invalidas(self):
        for campo, valor in [('latitude', '90.0000001'), ('latitude', '-90.0000001'),
                             ('longitude', '180.0000001'), ('longitude', '-180.0000001'),
                             ('latitude', 'NaN'), ('longitude', 'Infinity')]:
            with self.subTest(campo=campo, valor=valor):
                self.assertEqual(self.registrar(**{campo: valor}).status_code, 400)
        self.assertEqual(Localizacao.objects.count(), 0)

    def test_limites_geograficos_validos(self):
        self.assertEqual(self.registrar(latitude='90', longitude='180').status_code, 201)
        self.assertEqual(self.registrar(latitude='-90', longitude='-180').status_code, 201)

    def test_precisao_invalida(self):
        for valor in [-1, 'NaN', 'Infinity', '-Infinity']:
            with self.subTest(valor=valor):
                self.assertEqual(self.registrar(precisao_metros=valor).status_code, 400)

    def test_data_futura_e_data_ausente(self):
        self.assertEqual(self.registrar(capturado_em=(timezone.now() + timedelta(minutes=10)).isoformat()).status_code, 400)
        data = self.payload()
        del data['capturado_em']
        self.assertEqual(self.client.post('/api/localizacoes/', data, format='json').status_code, 400)

    def test_compartilhamento_desativado_bloqueia_novos_registros(self):
        self.assertEqual(self.registrar().status_code, 201)
        response = self.client.patch(f'/api/pessoas/{self.pessoa.pk}/', {'compartilhamento_ativo': False}, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.registrar().status_code, 400)
        self.assertEqual(self.client.get('/api/localizacoes/').data['count'], 1)

    def test_dispositivo_inativo_bloqueia_registro(self):
        self.dispositivo.ativo = False
        self.dispositivo.save()
        self.assertEqual(self.registrar().status_code, 400)

    def test_historico_e_ultima_posicao_usam_data_de_captura(self):
        recente = self.registrar()
        antiga = self.registrar(capturado_em=(timezone.now() - timedelta(days=1)).isoformat())
        response = self.client.get('/api/localizacoes/')
        self.assertEqual([item['id'] for item in response.data['results']], [recente.data['id'], antiga.data['id']])
        latest = self.client.get(f'/api/pessoas/{self.pessoa.pk}/ultima-localizacao/')
        self.assertEqual(latest.data['id'], recente.data['id'])

    def test_pessoa_sem_localizacao(self):
        self.assertEqual(self.client.get(f'/api/pessoas/{self.pessoa.pk}/ultima-localizacao/').status_code, 404)

    def test_filtros_de_periodo_e_dispositivo(self):
        self.assertEqual(self.registrar(capturado_em=(timezone.now() - timedelta(days=2)).isoformat()).status_code, 201)
        recente = self.registrar()
        response = self.client.get('/api/localizacoes/', {
            'inicio': (timezone.now() - timedelta(days=1)).isoformat(),
            'fim': (timezone.now() + timedelta(minutes=1)).isoformat(),
            'dispositivo': str(self.dispositivo.pk), 'pessoa': str(self.pessoa.pk),
        })
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['id'], recente.data['id'])

    def test_filtros_invalidos_retornam_400(self):
        for params in [{'pessoa': 'invalido'}, {'dispositivo': 'invalido'}, {'inicio': 'ontem'},
                       {'inicio': '2026-09-25T12:00:00Z', 'fim': '2026-09-24T12:00:00Z'}]:
            with self.subTest(params=params):
                self.assertEqual(self.client.get('/api/localizacoes/', params).status_code, 400)

    def test_historico_nao_permite_editar_ou_excluir_registro_individual(self):
        criada = self.registrar()
        url = f"/api/localizacoes/{criada.data['id']}/"
        self.assertEqual(self.client.patch(url, {'latitude': '0'}, format='json').status_code, 405)
        self.assertEqual(self.client.delete(url).status_code, 405)

    def test_exclusao_de_pessoa_remove_dispositivo_e_historico(self):
        self.assertEqual(self.registrar().status_code, 201)
        self.assertEqual(self.client.delete(f'/api/pessoas/{self.pessoa.pk}/').status_code, 204)
        self.assertFalse(Dispositivo.objects.filter(pk=self.dispositivo.pk).exists())
        self.assertEqual(Localizacao.objects.count(), 0)

    def test_paginacao(self):
        Pessoa.objects.bulk_create([Pessoa(nome=f'Pessoa {i}', responsavel=self.usuario) for i in range(55)])
        response = self.client.get('/api/pessoas/')
        self.assertEqual(response.data['count'], 56)
        self.assertEqual(len(response.data['results']), 50)
        self.assertIsNotNone(response.data['next'])

    def test_admin_restrito_a_superusuario_mesmo_com_permissoes(self):
        self.usuario.is_staff = True
        self.usuario.save()
        self.usuario.user_permissions.set(Permission.objects.filter(content_type__app_label='rastreamento'))
        self.client.force_login(self.usuario)
        self.assertEqual(self.client.get('/admin/rastreamento/pessoa/').status_code, 403)
        self.usuario.is_superuser = True
        self.usuario.save()
        self.assertEqual(self.client.get('/admin/rastreamento/pessoa/').status_code, 200)

    def test_banco_rejeita_coordenadas_fora_dos_limites(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            Localizacao.objects.create(dispositivo=self.dispositivo, latitude=Decimal('91'),
                                       longitude=Decimal('0'), capturado_em=timezone.now())
