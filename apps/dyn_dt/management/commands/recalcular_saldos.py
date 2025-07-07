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
                # Calcular saldos por separado
                saldo_caja_actual = caja.saldo_caja
                saldo_banco_actual = caja.saldo_banco
                saldo_total_actual = caja.saldo
                
                saldo_caja_calculado = sum(
                    mov.cantidad_real() for mov in caja.movimientos.all()
                )
                saldo_banco_calculado = sum(
                    mov.cantidad_real() for mov in caja.movimientos_banco.all()
                )
                saldo_total_calculado = saldo_caja_calculado + saldo_banco_calculado
                
                # Verificar inconsistencias
                inconsistencia_caja = saldo_caja_actual != saldo_caja_calculado
                inconsistencia_banco = saldo_banco_actual != saldo_banco_calculado
                inconsistencia_total = saldo_total_actual != saldo_total_calculado
                
                if inconsistencia_caja or inconsistencia_banco or inconsistencia_total:
                    inconsistencias += 1
                    self.stdout.write(
                        self.style.WARNING(
                            f'Caja "{caja.nombre}": INCONSISTENCIAS DETECTADAS'
                        )
                    )
                    
                    if inconsistencia_caja:
                        self.stdout.write(
                            f'  Saldo caja: {saldo_caja_actual}€ (actual) vs {saldo_caja_calculado}€ (calculado)'
                        )
                    
                    if inconsistencia_banco:
                        self.stdout.write(
                            f'  Saldo banco: {saldo_banco_actual}€ (actual) vs {saldo_banco_calculado}€ (calculado)'
                        )
                    
                    if inconsistencia_total:
                        self.stdout.write(
                            f'  Saldo total: {saldo_total_actual}€ (actual) vs {saldo_total_calculado}€ (calculado)'
                        )
                    
                    if not verificar_solo:
                        caja.saldo_caja = saldo_caja_calculado
                        caja.saldo_banco = saldo_banco_calculado
                        caja.saldo = saldo_total_calculado
                        caja.save(skip_validation=True)  # Saltamos validación para el recálculo
                        correcciones += 1
                        self.stdout.write(
                            self.style.SUCCESS(
                                f'  ✓ Corregido -> Caja: {saldo_caja_calculado}€, '
                                f'Banco: {saldo_banco_calculado}€, '
                                f'Total: {saldo_total_calculado}€'
                            )
                        )
                else:
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'Caja "{caja.nombre}": ✓ Saldo correcto '
                            f'(Caja: {saldo_caja_actual}€, Banco: {saldo_banco_actual}€, Total: {saldo_total_actual}€)'
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
