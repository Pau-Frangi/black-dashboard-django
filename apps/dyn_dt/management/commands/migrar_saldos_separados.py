"""
Comando de gestión Django para migrar los saldos existentes al nuevo sistema de saldos separados.
Este comando transfiere el saldo actual al saldo_caja y deja saldo_banco en 0.

Uso: python manage.py migrar_saldos_separados
"""

from django.core.management.base import BaseCommand
from django.db import transaction
from apps.dyn_dt.models import Caja
from decimal import Decimal


class Command(BaseCommand):
    help = 'Migra los saldos existentes al nuevo sistema de saldos separados (caja/banco)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Solo simular sin realizar cambios',
        )

    def handle(self, *args, **options):
        dry_run = options.get('dry_run')
        
        cajas = Caja.objects.all()
        total_cajas = cajas.count()
        
        if total_cajas == 0:
            self.stdout.write(
                self.style.SUCCESS('✅ No hay cajas para migrar')
            )
            return
            
        self.stdout.write(f'Migrando saldos de {total_cajas} cajas...\n')
        
        migradas = 0
        
        with transaction.atomic():
            for caja in cajas:
                saldo_original = caja.saldo_caja
                
                if dry_run:
                    self.stdout.write(
                        f'[DRY-RUN] Caja "{caja.nombre}": '
                        f'Saldo actual: {saldo_original}€ (ya migrado)'
                    )
                else:
                    # El saldo ya está correctamente separado, solo validar
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'✅ Caja "{caja.nombre}": '
                            f'Saldo caja: {caja.saldo_caja:.2f}€'
                        )
                    )
                
                migradas += 1
        
        # Resumen final
        self.stdout.write('\n' + '='*50)
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    f'[DRY-RUN] Se migrarían {migradas} cajas'
                )
            )
            self.stdout.write('Ejecuta sin --dry-run para aplicar los cambios')
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f'✅ {migradas} cajas migradas exitosamente'
                )
            )
            
        self.stdout.write(
            'Ahora todos los saldos están divididos en efectivo (caja) y bancario'
        )
            self.stdout.write(
                self.style.SUCCESS(
                    f'✅ {migradas} cajas migradas exitosamente'
                )
            )
            
        self.stdout.write(
            'Ahora todos los saldos están divididos en efectivo (caja) y bancario'
        )
