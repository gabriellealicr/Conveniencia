# Generated by Django 4.2.2 on 2023-07-04 16:48

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('produtos', '0002_alter_produto_codigo_barras'),
    ]

    operations = [
        migrations.CreateModel(
            name='Tipo',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nome', models.CharField(max_length=50, null=True)),
            ],
        ),
        migrations.AddField(
            model_name='produto',
            name='tipo',
            field=models.BooleanField(null=1),
            preserve_default=1,
        ),
    ]
