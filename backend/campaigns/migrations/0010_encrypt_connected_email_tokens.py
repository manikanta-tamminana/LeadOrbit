from django.db import migrations, models
from campaigns.fields import EncryptedTextField


def encrypt_existing_tokens(apps, schema_editor):
    from campaigns.fields import encrypt_token

    Account = apps.get_model('campaigns', 'ConnectedEmailAccount')
    database = schema_editor.connection.alias
    for account in Account._base_manager.using(database).all().iterator():
        updates = {}
        for name in ('access_token', 'refresh_token'):
            value = getattr(account, name)
            if value:
                updates[name] = encrypt_token(value)
        if updates:
            Account._base_manager.using(database).filter(pk=account.pk).update(**updates)


def decrypt_existing_tokens(apps, schema_editor):
    from campaigns.fields import decrypt_token

    Account = apps.get_model('campaigns', 'ConnectedEmailAccount')
    database = schema_editor.connection.alias
    for account in Account._base_manager.using(database).all().iterator():
        updates = {}
        for name in ('access_token', 'refresh_token'):
            value = getattr(account, name)
            if value:
                updates[name] = decrypt_token(value)
        if updates:
            Account._base_manager.using(database).filter(pk=account.pk).update(**updates)


class Migration(migrations.Migration):
    dependencies = [
        ('campaigns', '0009_campaign_cached_counters'),
        ('campaigns', '0009_campaignlead_bounce_metadata'),
    ]

    operations = [
        migrations.RunPython(encrypt_existing_tokens, decrypt_existing_tokens),
        migrations.AlterField(
            model_name='connectedemailaccount',
            name='access_token',
            field=EncryptedTextField(),
        ),
        migrations.AlterField(
            model_name='connectedemailaccount',
            name='refresh_token',
            field=EncryptedTextField(blank=True, null=True),
        ),
    ]
