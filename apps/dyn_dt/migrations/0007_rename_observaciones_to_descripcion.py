# Generated by Django 4.2.9 on 2025-01-XX XX:XX

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dyn_dt', '0006_alter_movimientocaja_fecha'),
    ]

    operations = [
        migrations.RenameField(
            model_name='movimientocaja',
            old_name='observaciones',
            new_name='descripcion',
        ),
        migrations.AlterField(
            model_name='movimientocaja',
            name='descripcion',
            field=models.TextField(help_text='Descripción detallada del movimiento', verbose_name='Descripción'),
        ),
    ]
