"""
Comando de gestión Django para recalcular los saldos de todas las cajas.
Uso: python manage.py recalcular_saldos
"""

from django.core.management.base import BaseCommand
from django.db import transaction
from apps.dyn_dt.models import Caja


class Command(BaseCommand):
    help = 'Recalcula los saldos de todas las cajas basándose en sus movimientos'

    def add_arguments(self, parser):
        parser.add_argument(
            '--caja-id',
            type=int,
            help='ID de una caja específica para recalcular (opcional)',
        )
        parser.add_argument(
            '--verificar-solo',
            action='store_true',
            help='Solo verificar inconsistencias sin corregir',
        )

    def handle(self, *args, **options):
        caja_id = options.get('caja_id')
        verificar_solo = options.get('verificar_solo')
        
        if caja_id:
            cajas = Caja.objects.filter(id=caja_id)
            if not cajas.exists():
                self.stdout.write(
                    self.style.ERROR(f'Caja con ID {caja_id} no encontrada')
                )
                return
        else:
            cajas = Caja.objects.all()

        inconsistencias = 0
        correcciones = 0

        self.stdout.write('Verificando saldos de cajas...\n')

        with transaction.atomic():
            for caja in cajas:
                saldo_actual = caja.saldo
                saldo_calculado = sum(
                    mov.cantidad_real() for mov in caja.movimientos.all()
                )
                
                if saldo_actual != saldo_calculado:
                    inconsistencias += 1
                    self.stdout.write(
                        self.style.WARNING(
                            f'Caja "{caja.nombre}": '
                            f'Saldo actual: {saldo_actual}€, '
                            f'Saldo calculado: {saldo_calculado}€'
                        )
                    )
                    
                    if not verificar_solo:
                        caja.saldo = saldo_calculado
                        caja.save(skip_validation=True)  # Saltamos validación para el recálculo
                        correcciones += 1
                        self.stdout.write(
                            self.style.SUCCESS(f'✓ Corregido a {saldo_calculado}€')
                        )
                else:
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'Caja "{caja.nombre}": ✓ Saldo correcto ({saldo_actual}€)'
                        )
                    )

        self.stdout.write('\n' + '='*50)
        if inconsistencias == 0:
            self.stdout.write(
                self.style.SUCCESS('✅ Todos los saldos están correctos')
            )
        else:
            if verificar_solo:
                self.stdout.write(
                    self.style.WARNING(
                        f'⚠️  {inconsistencias} inconsistencias encontradas'
                    )
                )
                self.stdout.write(
                    'Ejecuta sin --verificar-solo para corregir'
                )
            else:
                self.stdout.write(
                    self.style.SUCCESS(
                        f'✅ {correcciones} saldos corregidos'
                    )
                )
