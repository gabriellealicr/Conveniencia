# Generated by Django 4.2.2 on 2023-07-15 20:45

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('estoque', '0004_movimentacaoestoque_quantidade'),
    ]

    operations = [
        migrations.RenameField(
            model_name='movimentacaoestoque',
            old_name='quantidade',
            new_name='quantidade_alteracao',
        ),
    ]