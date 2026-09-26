"""Limpeza explícita e limitada. Não define uma política de retenção."""
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone
from django.utils.dateparse import parse_datetime

from rastreamento.models import LinkDispositivo, Localizacao


class Command(BaseCommand):
    help = 'Simula ou executa limpeza de posições recebidas/links expirados antes de uma data explícita.'

    def add_arguments(self, parser):
        parser.add_argument('--tipo', required=True, choices=['localizacoes', 'links'])
        parser.add_argument('--antes', required=True, help='Data ISO com fuso; limite exclusivo, preservado entre simulação e execução.')
        scope = parser.add_mutually_exclusive_group(required=True)
        scope.add_argument('--responsavel', type=int)
        scope.add_argument('--todos', action='store_true')
        parser.add_argument('--confirmar', action='store_true', help='Exclui registros. Sem esta opção, apenas simula.')
        parser.add_argument('--esperados', type=int, help='Quantidade da simulação; obrigatória para confirmar.')
        parser.add_argument('--maximo', type=int, default=1000, help='Limite de exclusões por execução; padrão: 1000.')

    def handle(self, *args, **options):
        try:
            cutoff = parse_datetime(options['antes'])
        except (TypeError, ValueError):
            cutoff = None
        if cutoff is None or timezone.is_naive(cutoff) or cutoff > timezone.now():
            raise CommandError('Informe --antes como data válida com fuso, sem usar uma data futura.')
        maximum = options['maximo']
        expected = options['esperados']
        if maximum < 1 or maximum > 100000:
            raise CommandError('--maximo deve estar entre 1 e 100000.')
        if expected is not None and expected < 0:
            raise CommandError('--esperados não pode ser negativo.')
        if options['confirmar'] and expected is None:
            raise CommandError('Execute a simulação e informe --esperados antes de confirmar.')
        owner = options['responsavel']
        if owner is not None and not get_user_model().objects.filter(pk=owner).exists():
            raise CommandError('Responsável não encontrado; nenhuma exclusão realizada.')
        if options['tipo'] == 'localizacoes':
            # Recebimento protege capturas atrasadas que acabaram de chegar.
            queryset = Localizacao.objects.filter(recebido_em__lt=cutoff)
        else:
            # Somente links cuja validade terminou antes do limite explícito.
            queryset = LinkDispositivo.objects.filter(expira_em__lt=cutoff)
        if owner is not None:
            queryset = queryset.filter(dispositivo__pessoa__responsavel_id=owner)
        self.stdout.write(f'Tipo: {options["tipo"]}; limite exclusivo: {cutoff.isoformat()}.')
        if not options['confirmar']:
            self.stdout.write(f'SIMULAÇÃO: {queryset.count()} registros elegíveis; nenhuma exclusão realizada.')
            self.stdout.write('A execução exige --confirmar e --esperados com a quantidade revisada; mantenha o mesmo limite e escopo.')
            return
        with transaction.atomic():
            ids = list(queryset.select_for_update().order_by('pk').values_list('pk', flat=True)[:maximum + 1])
            if len(ids) > maximum:
                raise CommandError('Quantidade acima de --maximo; nenhuma exclusão realizada. Revise o escopo.')
            if len(ids) != expected:
                raise CommandError('A quantidade difere de --esperados; nenhuma exclusão realizada. Simule novamente.')
            deleted, _ = queryset.filter(pk__in=ids).delete()
        self.stdout.write(self.style.SUCCESS(f'EXCLUSÃO CONCLUÍDA: {deleted} registros removidos do banco ativo.'))
        self.stdout.write('Backups, arquivos sincronizados e registros externos não foram alterados.')
