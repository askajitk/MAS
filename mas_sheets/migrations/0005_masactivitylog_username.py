from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("mas_sheets", "0004_mas_is_latest_mas_parent_mas_alter_mas_mas_id"),
    ]

    operations = [
        migrations.AddField(
            model_name="masactivitylog",
            name="username",
            field=models.CharField(max_length=150, blank=True),
        ),
    ]
