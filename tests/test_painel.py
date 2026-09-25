from datetime import timedelta
from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from django.utils import timezone
from rastreamento.models import Pessoa, Dispositivo, Localizacao


class PainelTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = get_user_model().objects.create_user(username='responsavel', password='Teste-Painel-123!')
        cls.outro = get_user_model().objects.create_user(username='outro')
        cls.pessoa = Pessoa.objects.create(nome='Minha pessoa', responsavel=cls.user)
        cls.alheia = Pessoa.objects.create(nome='Pessoa privada', responsavel=cls.outro)
        cls.dispositivo = Dispositivo.objects.create(nome='Meu celular', pessoa=cls.pessoa)

    def setUp(self):
        self.client.force_login(self.user)

    def test_login_obrigatorio_e_tela_de_login(self):
        self.client.logout()
        self.assertRedirects(self.client.get('/'), '/entrar/?next=/')
        self.assertContains(self.client.get('/entrar/'), 'Entrar no painel')

    def test_painel_renderiza_sem_vazar_pessoas(self):
        response = self.client.get('/')
        self.assertContains(response, 'Minha pessoa')
        self.assertNotContains(response, 'Pessoa privada')
        self.assertContains(response, 'Ainda não há posições')
        self.assertIn('no-store', response.headers['Cache-Control'])

    def test_selecao_alheia_e_uuid_invalido_retornam_404(self):
        self.assertEqual(self.client.get('/', {'pessoa': self.alheia.pk}).status_code, 404)
        self.assertEqual(self.client.get('/', {'pessoa': 'invalido'}).status_code, 404)

    def test_cadastro_pessoa_sem_compartilhamento_automatico(self):
        self.client.post('/painel/pessoas/', {'nome': 'Nova', 'compartilhamento_ativo': True, 'responsavel': self.outro.pk})
        nova = Pessoa.objects.get(nome='Nova')
        self.assertEqual(nova.responsavel, self.user)
        self.assertFalse(nova.compartilhamento_ativo)

    def test_dispositivo_proprio_aceito_alheio_recusado(self):
        self.client.post('/painel/dispositivos/', {'nome': 'Novo dispositivo', 'pessoa': self.pessoa.pk})
        self.assertTrue(Dispositivo.objects.filter(nome='Novo dispositivo', pessoa=self.pessoa).exists())
        self.client.post('/painel/dispositivos/', {'nome': 'Invasor', 'pessoa': self.alheia.pk})
        self.assertFalse(Dispositivo.objects.filter(nome='Invasor').exists())

    def test_ativacao_exige_confirmacao_e_desativacao_funciona(self):
        url = f'/painel/pessoas/{self.pessoa.pk}/compartilhamento/'
        self.client.post(url, {'ativo': 'true'})
        self.pessoa.refresh_from_db()
        self.assertFalse(self.pessoa.compartilhamento_ativo)
        self.client.post(url, {'ativo': 'true', 'autorizado': 'on'})
        self.pessoa.refresh_from_db()
        self.assertTrue(self.pessoa.compartilhamento_ativo)
        self.client.post(url, {'ativo': 'false'})
        self.pessoa.refresh_from_db()
        self.assertFalse(self.pessoa.compartilhamento_ativo)

    def test_compartilhamento_alheio_bloqueado(self):
        self.assertEqual(self.client.post(f'/painel/pessoas/{self.alheia.pk}/compartilhamento/', {'ativo': 'true', 'autorizado': 'on'}).status_code, 404)

    def test_formularios_exigem_csrf_e_post(self):
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.user)
        self.assertEqual(client.post('/painel/pessoas/', {'nome': 'Teste'}).status_code, 403)
        self.assertEqual(self.client.get('/painel/pessoas/').status_code, 405)

    def test_posicao_antiga_paginacao_e_json_seguro(self):
        self.dispositivo.nome = '</script><script>alert(1)</script>'
        self.dispositivo.save()
        Localizacao.objects.bulk_create([Localizacao(dispositivo=self.dispositivo, latitude=-3.7, longitude=-38.5, capturado_em=timezone.now()-timedelta(hours=1, minutes=i)) for i in range(21)])
        response = self.client.get('/')
        self.assertContains(response, 'Posição antiga')
        self.assertEqual(len(response.context['pontos']), 20)
        self.assertEqual(response.context['pagina'].paginator.count, 21)
        self.assertNotContains(response, '</script><script>alert(1)</script>')
        self.assertContains(response, '\\u003C/script\\u003E')
        self.assertEqual(len(self.client.get('/', {'pagina': 2}).context['pontos']), 1)

    def test_estado_vazio_e_logout_post(self):
        self.client.force_login(self.outro)
        self.alheia.delete()
        self.assertContains(self.client.get('/'), 'Nenhuma pessoa cadastrada')
        self.assertEqual(self.client.get('/sair/').status_code, 405)
        self.assertRedirects(self.client.post('/sair/'), '/entrar/')
