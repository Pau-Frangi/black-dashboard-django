#!/usr/bin/env python
"""
Script de prueba para verificar que las señales Django funcionan correctamente
para bulk deletes (eliminaciones masivas) como las del admin de Django.
"""

import os
import django
from decimal import Decimal

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.dyn_dt.models import Caja, Turno, Concepto, MovimientoCaja


def test_bulk_delete():
    """Prueba que el saldo se actualice correctamente con bulk delete"""
    
    print("=== PRUEBA DE BULK DELETE ===\n")
    
    # Crear datos de prueba
    caja, created = Caja.objects.get_or_create(
        nombre="Caja Bulk Test",
        defaults={
            'año': 2025,
            'saldo': Decimal('0.00'),
            'activa': True
        }
    )
    
    turno, created = Turno.objects.get_or_create(
        ejercicio=caja.ejercicio,
        nombre="Turno Bulk Test"
    )
    
    concepto_ingreso, created = Concepto.objects.get_or_create(
        nombre="Ingreso Bulk",
        defaults={'es_gasto': False}
    )
    
    concepto_gasto, created = Concepto.objects.get_or_create(
        nombre="Gasto Bulk", 
        defaults={'es_gasto': True}
    )
    
    # Reset saldo inicial
    caja.saldo = Decimal('0.00')
    caja.save()
    
    print(f"Saldo inicial: {caja.saldo}")
    
    # Crear múltiples movimientos
    movimientos_ingreso = []
    movimientos_gasto = []
    
    # 3 ingresos de 50€ cada uno = +150€
    for i in range(3):
        mov = MovimientoCaja.objects.create(
            caja=caja,
            turno=turno,
            concepto=concepto_ingreso,
            cantidad=Decimal('50.00'),
            descripcion=f"Ingreso bulk {i+1}"
        )
        movimientos_ingreso.append(mov)
    
    # 2 gastos de 25€ cada uno = -50€
    for i in range(2):
        mov = MovimientoCaja.objects.create(
            caja=caja,
            turno=turno,
            concepto=concepto_gasto,
            cantidad=Decimal('25.00'),
            descripcion=f"Gasto bulk {i+1}"
        )
        movimientos_gasto.append(mov)
    
    # Recargar la caja para ver el saldo actualizado
    caja.refresh_from_db()
    print(f"Después de crear movimientos (+150-50): {caja.saldo}")
    assert caja.saldo == Decimal('100.00'), f"Esperado 100.00, obtenido {caja.saldo}"
    
    # BULK DELETE de movimientos de gasto (debe sumar +50 al saldo)
    print("\nEliminando gastos con bulk delete...")
    ids_gastos = [mov.id for mov in movimientos_gasto]
    MovimientoCaja.objects.filter(id__in=ids_gastos).delete()
    
    # Recargar la caja para ver el saldo actualizado
    caja.refresh_from_db()
    print(f"Después de bulk delete gastos (+50): {caja.saldo}")
    assert caja.saldo == Decimal('150.00'), f"Esperado 150.00, obtenido {caja.saldo}"
    
    # BULK DELETE de movimientos de ingreso (debe restar -150 al saldo)
    print("\nEliminando ingresos con bulk delete...")
    ids_ingresos = [mov.id for mov in movimientos_ingreso]
    MovimientoCaja.objects.filter(id__in=ids_ingresos).delete()
    
    # Recargar la caja para ver el saldo actualizado
    caja.refresh_from_db()
    print(f"Después de bulk delete ingresos (-150): {caja.saldo}")
    assert caja.saldo == Decimal('0.00'), f"Esperado 0.00, obtenido {caja.saldo}"
    
    print("\n✅ BULK DELETE FUNCIONA CORRECTAMENTE")
    print("Las señales Django manejan correctamente las eliminaciones masivas")
    
    # Limpiar datos de prueba
    caja.delete()
    turno.delete()
    concepto_ingreso.delete()
    concepto_gasto.delete()


if __name__ == "__main__":
    test_bulk_delete()
