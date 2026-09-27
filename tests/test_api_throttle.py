from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import TestCase
from rest_framework.test import APIClient

from rastreamento.models import Pessoa


class APILimitTests(TestCase):
    def setUp(self):
        cache.clear()
        self.addCleanup(cache.clear)
        self.owner = get_user_model().objects.create_user('limite_ficticio')
        self.other = get_user_model().objects.create_user('outro_limite_ficticio')
        self.api = APIClient()
        self.api.force_authenticate(self.owner)

    def test_default_limit_blocks_write_and_does_not_block_other_account(self):
        with patch('rest_framework.throttling.SimpleRateThrottle.timer', return_value=1000):
            for _ in range(120):
                self.assertEqual(self.api.get('/api/aviso-envio/').status_code, 200)
            rejected = self.api.post('/api/pessoas/', {'nome': 'Não deve ser criada'}, format='json')
            self.assertEqual(rejected.status_code, 429)
            self.assertEqual(rejected['Retry-After'], '60')
            self.assertIn('no-store', rejected['Cache-Control'])
            self.assertFalse(Pessoa.objects.exists())
            self.api.force_authenticate(self.other)
            self.assertEqual(self.api.get('/api/aviso-envio/').status_code, 200)
        self.api.force_authenticate(self.owner)
        with patch('rest_framework.throttling.SimpleRateThrottle.timer', return_value=1061):
            self.assertEqual(self.api.get('/api/aviso-envio/').status_code, 200)
