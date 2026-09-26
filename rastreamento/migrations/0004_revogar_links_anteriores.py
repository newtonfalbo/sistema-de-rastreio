from django.db import migrations
from django.utils import timezone


def revogar_pendentes(apps, schema_editor):
    Link = apps.get_model('rastreamento', 'LinkDispositivo')
    Link.objects.using(schema_editor.connection.alias).filter(
        utilizado_em__isnull=True, revogado_em__isnull=True,
    ).update(revogado_em=timezone.now())


class Migration(migrations.Migration):
    dependencies = [('rastreamento', '0003_localizacao_autorizacao_recebida_em_and_more')]
    operations = [migrations.RunPython(revogar_pendentes, reverse_code=migrations.RunPython.noop)]
