# Generated manually on 2025-07-12
# Remove old saldo and saldo_banco fields from Caja model

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dyn_dt', '0013_ejercicio_caja_ejercicio'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='caja',
            name='saldo',
        ),
        migrations.RemoveField(
            model_name='caja',
            name='saldo_banco',
        ),
    ]
