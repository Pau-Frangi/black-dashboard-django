# Generated manually on 2025-07-12
# Update MovimientoBanco to use ejercicio instead of caja, turno

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('dyn_dt', '0014_remove_old_saldo_fields'),
    ]

    operations = [
        # Remove old fields from MovimientoBanco
        migrations.RemoveField(
            model_name='movimientobanco',
            name='caja',
        ),
        migrations.RemoveField(
            model_name='movimientobanco',
            name='turno',
        ),
        migrations.RemoveField(
            model_name='movimientobanco',
            name='justificante',
        ),
        # Add ejercicio field to MovimientoBanco
        migrations.AddField(
            model_name='movimientobanco',
            name='ejercicio',
            field=models.ForeignKey(
                default=1,  # Use existing ejercicio as default
                on_delete=django.db.models.deletion.CASCADE,
                related_name='movimientos_banco',
                to='dyn_dt.ejercicio',
                verbose_name='Ejercicio'
            ),
            preserve_default=False,
        ),
    ]
