from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("services", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="servicelog",
            name="username",
            field=models.CharField(max_length=150, null=True, blank=True),
        ),
    ]
