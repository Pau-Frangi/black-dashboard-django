# Generated by Django 4.2.9 on 2025-07-16 19:29

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('dyn_dt', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='movimientobanco',
            name='turno',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, related_name='movimientos_banco', to='dyn_dt.turno', verbose_name='Turno'),
            preserve_default=False,
        ),
    ]
