# Generated by Django 5.0.2 on 2024-04-09 03:58

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Usuarios', '0005_linea_codigo_linea'),
    ]

    operations = [
        migrations.AddField(
            model_name='linea',
            name='area',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='Usuarios.area'),
        ),
    ]