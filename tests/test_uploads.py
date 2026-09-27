from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from unittest.mock import patch
from rest_framework.test import APIClient

from rastreamento.models import Pessoa


class UnexpectedUploadTests(TestCase):
    def setUp(self):
        self.owner = get_user_model().objects.create_user('upload_ficticio')
        self.api = APIClient()
        self.api.force_authenticate(self.owner)

    @override_settings(FILE_UPLOAD_HANDLERS=['django.core.files.uploadhandler.TemporaryFileUploadHandler'])
    def test_api_refuses_file_without_creating_person(self):
        with patch('django.core.files.uploadhandler.TemporaryFileUploadHandler.new_file') as begin_file:
            response = self.api.post('/api/pessoas/', {
                'nome': 'Cadastro fictício',
                'anexo': SimpleUploadedFile('ficticio.txt', b'conteudo ficticio'),
            }, format='multipart')
        begin_file.assert_not_called()
        self.assertEqual(response.status_code, 400)
        self.assertFalse(Pessoa.objects.exists())

    def test_panel_refuses_file_without_creating_person(self):
        self.client.force_login(self.owner)
        response = self.client.post('/painel/pessoas/', {
            'nome': 'Cadastro fictício',
            'anexo': SimpleUploadedFile('ficticio.txt', b'conteudo ficticio'),
        })
        self.assertEqual(response.status_code, 400)
        self.assertFalse(Pessoa.objects.exists())

    def test_multipart_without_file_still_accepts_normal_fields(self):
        response = self.api.post('/api/pessoas/', {'nome': 'Cadastro fictício'}, format='multipart')
        self.assertEqual(response.status_code, 201)
        self.assertEqual(Pessoa.objects.count(), 1)
