# Generated by Django 4.2.9 on 2025-07-04 11:46

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('dyn_dt', '0008_movimientocaja_archivo_justificante'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='turno',
            options={'ordering': ['caja__nombre', 'nombre'], 'verbose_name': 'Turno', 'verbose_name_plural': 'Turnos'},
        ),
        migrations.AddField(
            model_name='turno',
            name='caja',
            field=models.ForeignKey(default=0, help_text='Caja a la que pertenece este turno', on_delete=django.db.models.deletion.CASCADE, related_name='turnos', to='dyn_dt.caja', verbose_name='Caja'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='turno',
            name='nombre',
            field=models.CharField(max_length=100, verbose_name='Nombre del turno'),
        ),
        migrations.AlterUniqueTogether(
            name='turno',
            unique_together={('caja', 'nombre')},
        ),
    ]
