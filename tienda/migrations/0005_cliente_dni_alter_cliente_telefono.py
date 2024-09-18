# Generated by Django 5.1.1 on 2024-09-18 05:23

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tienda', '0004_proveedor_vendedor_remove_cliente_dni_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='cliente',
            name='dni',
            field=models.CharField(default=0, max_length=8, unique=True),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='cliente',
            name='telefono',
            field=models.CharField(max_length=9),
        ),
    ]
