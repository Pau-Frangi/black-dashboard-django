"""
Comando de gestión Django para crear las denominaciones de euro por defecto.
Uso: python manage.py crear_denominaciones
"""

from django.core.management.base import BaseCommand
from apps.dyn_dt.models import DenominacionEuro
from decimal import Decimal


class Command(BaseCommand):
    help = 'Crea las denominaciones de euro por defecto (billetes y monedas)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--limpiar',
            action='store_true',
            help='Eliminar todas las denominaciones existentes antes de crear las nuevas',
        )

    def handle(self, *args, **options):
        if options.get('limpiar'):
            self.stdout.write('Eliminando denominaciones existentes...')
            DenominacionEuro.objects.all().delete()
            self.stdout.write(self.style.SUCCESS('✓ Denominaciones eliminadas'))

        # Definir las denominaciones estándar de euro
        denominaciones = [
            # Billetes
            (Decimal('500.00'), True, False),   # 500€ - Desactivado por defecto
            (Decimal('200.00'), True, False),   # 200€ - Desactivado por defecto
            (Decimal('100.00'), True, True),    # 100€
            (Decimal('50.00'), True, True),     # 50€
            (Decimal('20.00'), True, True),     # 20€
            (Decimal('10.00'), True, True),     # 10€
            (Decimal('5.00'), True, True),      # 5€
            
            # Monedas
            (Decimal('2.00'), False, True),     # 2€
            (Decimal('1.00'), False, True),     # 1€
            (Decimal('0.50'), False, True),     # 50 céntimos
            (Decimal('0.20'), False, True),     # 20 céntimos
            (Decimal('0.10'), False, True),     # 10 céntimos
            (Decimal('0.05'), False, True),     # 5 céntimos
            (Decimal('0.02'), False, False),    # 2 céntimos - Desactivado por defecto
            (Decimal('0.01'), False, False),    # 1 céntimo - Desactivado por defecto
        ]

        creadas = 0
        existentes = 0

        self.stdout.write('Creando denominaciones de euro...\n')

        for valor, es_billete, activa in denominaciones:
            denominacion, created = DenominacionEuro.objects.get_or_create(
                valor=valor,
                defaults={
                    'es_billete': es_billete,
                    'activa': activa
                }
            )
            
            if created:
                creadas += 1
                estado = "✓ CREADA"
                if not activa:
                    estado += " (INACTIVA)"
                self.stdout.write(
                    self.style.SUCCESS(f'{estado}: {denominacion}')
                )
            else:
                existentes += 1
                self.stdout.write(
                    self.style.WARNING(f'○ EXISTE: {denominacion}')
                )

        self.stdout.write('\n' + '='*50)
        self.stdout.write(
            self.style.SUCCESS(
                f'✅ Proceso completado: {creadas} creadas, {existentes} ya existían'
            )
        )
        
        if creadas > 0:
            self.stdout.write(
                'Las denominaciones inactivas (500€, 200€, 1 y 2 céntimos) '
                'se pueden activar desde el admin si son necesarias.'
            )
