"""
Comando de gestión Django para generar desglose obligatorio para movimientos existentes.
Este comando es necesario tras la migración a desglose obligatorio.

Uso: python manage.py generar_desglose_obligatorio
"""

from django.core.management.base import BaseCommand
from django.db import transaction
from apps.dyn_dt.models import MovimientoCaja, DenominacionEuro, MovimientoDinero
from decimal import Decimal


class Command(BaseCommand):
    help = 'Genera desglose automático para movimientos existentes sin desglose'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Solo simular sin realizar cambios',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Forzar la creación incluso si ya existe desglose',
        )

    def handle(self, *args, **options):
        dry_run = options.get('dry_run')
        force = options.get('force')
        
        movimientos_sin_desglose = MovimientoCaja.objects.filter(
            movimientos_dinero__isnull=True
        ).distinct()
        
        if force:
            # Si se fuerza, incluir todos los movimientos
            movimientos_sin_desglose = MovimientoCaja.objects.all()
            
        total_movimientos = movimientos_sin_desglose.count()
        
        if total_movimientos == 0:
            self.stdout.write(
                self.style.SUCCESS('✅ Todos los movimientos ya tienen desglose')
            )
            return
            
        self.stdout.write(f'Procesando {total_movimientos} movimientos...\n')
        
        # Obtener denominaciones activas ordenadas de mayor a menor
        denominaciones = DenominacionEuro.objects.filter(activa=True).order_by('-valor')
        
        if not denominaciones.exists():
            self.stdout.write(
                self.style.ERROR('❌ No hay denominaciones activas configuradas')
            )
            return
            
        procesados = 0
        errores = 0
        
        with transaction.atomic():
            for movimiento in movimientos_sin_desglose:
                try:
                    # Si no es dry-run y se fuerza, eliminar desglose existente
                    if force and not dry_run:
                        movimiento.movimientos_dinero.all().delete()
                    
                    desglose_generado = self.generar_desglose_automatico(
                        movimiento.cantidad, denominaciones
                    )
                    
                    if dry_run:
                        self.stdout.write(
                            f'[DRY-RUN] Movimiento {movimiento.id} '
                            f'({movimiento.cantidad}€): {desglose_generado}'
                        )
                    else:
                        # Crear los movimientos de dinero
                        for denominacion, cantidad in desglose_generado.items():
                            if cantidad > 0:
                                MovimientoDinero.objects.create(
                                    movimiento_caja=movimiento,
                                    denominacion=denominacion,
                                    cantidad_entrada=cantidad,
                                    cantidad_salida=0
                                )
                        
                        self.stdout.write(
                            self.style.SUCCESS(
                                f'✅ Movimiento {movimiento.id} procesado correctamente'
                            )
                        )
                    
                    procesados += 1
                    
                except Exception as e:
                    errores += 1
                    self.stdout.write(
                        self.style.ERROR(
                            f'❌ Error procesando movimiento {movimiento.id}: {str(e)}'
                        )
                    )
        
        # Resumen final
        self.stdout.write('\n' + '='*50)
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING(f'[DRY-RUN] Se procesarían {procesados} movimientos')
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(f'✅ {procesados} movimientos procesados')
            )
            
        if errores > 0:
            self.stdout.write(
                self.style.ERROR(f'❌ {errores} errores encontrados')
            )
            
    def generar_desglose_automatico(self, cantidad, denominaciones):
        """
        Genera un desglose automático usando denominaciones de mayor a menor
        """
        desglose = {}
        cantidad_restante = cantidad
        
        for denominacion in denominaciones:
            if cantidad_restante >= denominacion.valor:
                cantidad_unidades = int(cantidad_restante // denominacion.valor)
                desglose[denominacion] = cantidad_unidades
                cantidad_restante -= cantidad_unidades * denominacion.valor
                cantidad_restante = round(cantidad_restante, 2)
            else:
                desglose[denominacion] = 0
                
        # Si queda algo por cubrir (centavos), añadirlo a la denominación más pequeña
        if cantidad_restante > 0:
            denominacion_minima = denominaciones.order_by('valor').first()
            if denominacion_minima:
                # Convertir el resto a la denominación más pequeña
                cantidad_adicional = int(cantidad_restante / denominacion_minima.valor)
                if cantidad_adicional > 0:
                    desglose[denominacion_minima] += cantidad_adicional
                    
        return desglose
