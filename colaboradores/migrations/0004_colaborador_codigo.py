# Generated by Django 4.2.2 on 2023-07-27 19:28

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('colaboradores', '0003_colaborador_email'),
    ]

    operations = [
        migrations.AddField(
            model_name='colaborador',
            name='codigo',
            field=models.IntegerField(default=1, null=True),
        ),
    ]