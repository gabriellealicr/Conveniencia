# Generated by Django 4.2.2 on 2023-06-23 19:10

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('colaboradores', '__first__'),
        ('produtos', '0002_alter_produto_codigo_barras'),
    ]

    operations = [
        migrations.CreateModel(
            name='Compra',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('data', models.DateTimeField()),
                ('valor_total', models.FloatField(default=0)),
                ('colaborador', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='colaboradores.colaborador')),
                ('produtos', models.ManyToManyField(to='produtos.produto')),
            ],
        ),
    ]
