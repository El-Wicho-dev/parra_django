# Generated by Django 5.0.2 on 2024-04-07 18:24

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Usuarios', '0004_alter_area_area_alter_departamento_departamento_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='linea',
            name='codigo_linea',
            field=models.CharField(max_length=50, null=True),
        ),
    ]
