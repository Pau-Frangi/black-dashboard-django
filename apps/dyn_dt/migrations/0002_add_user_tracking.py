from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
        ('dyn_dt', '0001_initial'),  # Adjust this to your last migration
    ]

    operations = [
        # First add fields as nullable
        migrations.AddField(
            model_name='caja',
            name='creado_en',
            field=models.DateTimeField(auto_now_add=True, null=True, verbose_name='Creado en'),
        ),
        migrations.AddField(
            model_name='caja',
            name='creado_por',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='auth.user', verbose_name='Creado por'),
        ),
        migrations.AddField(
            model_name='concepto',
            name='creado_en',
            field=models.DateTimeField(auto_now_add=True, null=True, verbose_name='Creado en'),
        ),
        migrations.AddField(
            model_name='concepto',
            name='creado_por',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='auth.user', verbose_name='Creado por'),
        ),
        migrations.AddField(
            model_name='denominacioneuro',
            name='creado_en',
            field=models.DateTimeField(auto_now_add=True, null=True, verbose_name='Creado en'),
        ),
        migrations.AddField(
            model_name='denominacioneuro',
            name='creado_por',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='auth.user', verbose_name='Creado por'),
        ),
        migrations.AddField(
            model_name='desglosecaja',
            name='creado_en',
            field=models.DateTimeField(auto_now_add=True, null=True, verbose_name='Creado en'),
        ),
        migrations.AddField(
            model_name='desglosecaja',
            name='creado_por',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='auth.user', verbose_name='Creado por'),
        ),
        migrations.AddField(
            model_name='ejercicio',
            name='creado_en',
            field=models.DateTimeField(auto_now_add=True, null=True, verbose_name='Creado en'),
        ),
        migrations.AddField(
            model_name='ejercicio',
            name='creado_por',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='auth.user', verbose_name='Creado por'),
        ),
        migrations.AddField(
            model_name='movimientobanco',
            name='creado_en',
            field=models.DateTimeField(auto_now_add=True, null=True, verbose_name='Creado en'),
        ),
        migrations.AddField(
            model_name='movimientobanco',
            name='creado_por',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='auth.user', verbose_name='Creado por'),
        ),
        migrations.AddField(
            model_name='movimientocaja',
            name='creado_en',
            field=models.DateTimeField(auto_now_add=True, null=True, verbose_name='Creado en'),
        ),
        migrations.AddField(
            model_name='movimientocaja',
            name='creado_por',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='auth.user', verbose_name='Creado por'),
        ),
        migrations.AddField(
            model_name='movimientodinero',
            name='creado_en',
            field=models.DateTimeField(auto_now_add=True, null=True, verbose_name='Creado en'),
        ),
        migrations.AddField(
            model_name='movimientodinero',
            name='creado_por',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='auth.user', verbose_name='Creado por'),
        ),
        migrations.AddField(
            model_name='turno',
            name='creado_en',
            field=models.DateTimeField(auto_now_add=True, null=True, verbose_name='Creado en'),
        ),
        migrations.AddField(
            model_name='turno',
            name='creado_por',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='auth.user', verbose_name='Creado por'),
        ),
    ]
