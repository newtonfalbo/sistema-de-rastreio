from django.db import migrations


def revogar_tokens_inativos(apps, schema_editor):
    Token = apps.get_model('authtoken', 'Token')
    Token.objects.using(schema_editor.connection.alias).filter(user__is_active=False).delete()


class Migration(migrations.Migration):
    dependencies = [
        ('rastreamento', '0004_revogar_links_anteriores'),
        ('authtoken', '0004_alter_tokenproxy_options'),
    ]
    operations = [migrations.RunPython(revogar_tokens_inativos, reverse_code=migrations.RunPython.noop)]
