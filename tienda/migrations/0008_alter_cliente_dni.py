# Generated by Django 5.1.1 on 2024-09-18 05:34

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tienda', '0007_alter_cliente_dni'),
    ]

    operations = [
        migrations.AlterField(
            model_name='cliente',
            name='dni',
            field=models.CharField(max_length=8),
        ),
    ]
