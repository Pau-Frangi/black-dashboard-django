# Generated manually on 2025-07-07

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dyn_dt', '0011_add_movimiento_banco_and_split_saldos'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='movimientobanco',
            name='tipo_operacion',
        ),
    ]
