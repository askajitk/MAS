from django.db import migrations


def backfill_usernames(apps, schema_editor):
    MASActivityLog = apps.get_model('mas_sheets', 'MASActivityLog')
    for log in MASActivityLog.objects.filter(username="", user__isnull=False).select_related('user'):
        log.username = log.user.username
        log.save(update_fields=['username'])


class Migration(migrations.Migration):

    dependencies = [
        ("mas_sheets", "0005_masactivitylog_username"),
    ]

    operations = [
        migrations.RunPython(backfill_usernames, migrations.RunPython.noop),
    ]
