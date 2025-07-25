# Generated by Django 4.2.9 on 2025-07-25 17:05

import apps.dyn_dt.mixins
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('dyn_dt', '0015_remove_viamovimientobanco_via_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='MovimientoCajaRetiro',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('cantidad', models.DecimalField(decimal_places=2, help_text='Cantidad de dinero del movimiento de retiro', max_digits=10, verbose_name='Cantidad (€)')),
                ('fecha', models.DateTimeField(default=django.utils.timezone.now, help_text='Fecha y hora en que se realizó el movimiento de retiro', verbose_name='Fecha y hora del movimiento de retiro')),
                ('retirado_por', models.CharField(help_text='Nombre de la persona que realizó el retiro', max_length=100, verbose_name='Retirado por')),
                ('creado_en', models.DateTimeField(auto_now_add=True, help_text='Fecha y hora de creación del movimiento de retiro', verbose_name='Creado en')),
                ('caja', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='movimientos_caja_retiro', to='dyn_dt.caja', verbose_name='Caja')),
                ('campamento', models.ForeignKey(help_text='Campamento al que pertenece este movimiento de retiro', on_delete=django.db.models.deletion.CASCADE, related_name='movimientos_caja_retiro', to='dyn_dt.campamento', verbose_name='Campamento')),
                ('creado_por', models.ForeignKey(blank=True, help_text='Usuario que creó este movimiento de retiro', null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL, verbose_name='Creado por')),
                ('ejercicio', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='movimientos_caja_retiro', to='dyn_dt.ejercicio', verbose_name='Ejercicio')),
            ],
            options={
                'verbose_name': 'Movimiento de retiro en caja',
                'verbose_name_plural': 'Movimientos de retiro en caja',
                'ordering': ['-fecha'],
            },
            bases=(apps.dyn_dt.mixins.UserTrackingMixin, models.Model),
        ),
        migrations.CreateModel(
            name='MovimientoCajaDeposito',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('cantidad', models.DecimalField(decimal_places=2, help_text='Cantidad de dinero del movimiento de depósito', max_digits=10, verbose_name='Cantidad (€)')),
                ('fecha', models.DateTimeField(default=django.utils.timezone.now, help_text='Fecha y hora en que se realizó el movimiento de depósito', verbose_name='Fecha y hora del movimiento de depósito')),
                ('creado_en', models.DateTimeField(auto_now_add=True, help_text='Fecha y hora de creación del movimiento de depósito', verbose_name='Creado en')),
                ('caja', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='movimientos_caja_deposito', to='dyn_dt.caja', verbose_name='Caja')),
                ('campamento', models.ForeignKey(help_text='Campamento al que pertenece este movimiento de depósito', on_delete=django.db.models.deletion.CASCADE, related_name='movimientos_caja_deposito', to='dyn_dt.campamento', verbose_name='Campamento')),
                ('creado_por', models.ForeignKey(blank=True, help_text='Usuario que creó este movimiento de depósito', null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL, verbose_name='Creado por')),
                ('ejercicio', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='movimientos_caja_deposito', to='dyn_dt.ejercicio', verbose_name='Ejercicio')),
            ],
            options={
                'verbose_name': 'Movimiento de depósito en caja',
                'verbose_name_plural': 'Movimientos de depósito en caja',
                'ordering': ['-fecha'],
            },
            bases=(apps.dyn_dt.mixins.UserTrackingMixin, models.Model),
        ),
    ]
