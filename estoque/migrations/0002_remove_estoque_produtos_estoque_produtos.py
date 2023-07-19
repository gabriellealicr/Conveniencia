# Generated by Django 4.2.2 on 2023-07-07 20:22

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('produtos', '0009_alter_produto_tipo'),
        ('estoque', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='estoque',
            name='produtos',
        ),
        migrations.AddField(
            model_name='estoque',
            name='produtos',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, to='produtos.produto'),
            preserve_default=False,
        ),
    ]