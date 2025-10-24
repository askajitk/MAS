from django.db import migrations


def backfill_usernames(apps, schema_editor):
    ServiceLog = apps.get_model('services', 'ServiceLog')
    # For existing logs with a user FK and empty snapshot, copy the username
    for log in ServiceLog.objects.filter(username__isnull=True, user__isnull=False).select_related('user'):
        log.username = log.user.username
        log.save(update_fields=['username'])


class Migration(migrations.Migration):

    dependencies = [
        ("services", "0002_servicelog_username"),
    ]

    operations = [
        migrations.RunPython(backfill_usernames, migrations.RunPython.noop),
    ]
