#!/usr/bin/env python
"""
Script de prueba para verificar que las señales Django funcionan correctamente
para actualizar el saldo de la caja cuando se crean o eliminan movimientos.
"""

import os
import django
from decimal import Decimal

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.dyn_dt.models import Caja, Turno, Concepto, MovimientoCaja


def test_saldo_updates():
    """Prueba que el saldo se actualice correctamente"""
    
    print("=== PRUEBA DE ACTUALIZACIÓN DE SALDO ===\n")
    
    # Crear datos de prueba
    caja, created = Caja.objects.get_or_create(
        nombre="Caja de Prueba",
        defaults={
            'año': 2025,
            'saldo': Decimal('0.00'),
            'activa': True
        }
    )
    
    turno, created = Turno.objects.get_or_create(
        nombre="Turno de Prueba"
    )
    
    concepto_ingreso, created = Concepto.objects.get_or_create(
        nombre="Ingreso de Prueba",
        defaults={'es_gasto': False}
    )
    
    concepto_gasto, created = Concepto.objects.get_or_create(
        nombre="Gasto de Prueba", 
        defaults={'es_gasto': True}
    )
    
    # Reset saldo inicial
    caja.saldo = Decimal('0.00')
    caja.save()
    
    print(f"Saldo inicial: {caja.saldo}")
    
    # Crear movimiento de ingreso
    movimiento_ingreso = MovimientoCaja.objects.create(
        caja=caja,
        turno=turno,
        concepto=concepto_ingreso,
        cantidad=Decimal('100.00'),
        observaciones="Ingreso de prueba"
    )
    
    # Recargar la caja para ver el saldo actualizado
    caja.refresh_from_db()
    print(f"Después de ingreso (+100): {caja.saldo}")
    assert caja.saldo == Decimal('100.00'), f"Esperado 100.00, obtenido {caja.saldo}"
    
    # Crear movimiento de gasto
    movimiento_gasto = MovimientoCaja.objects.create(
        caja=caja,
        turno=turno,
        concepto=concepto_gasto,
        cantidad=Decimal('30.00'),
        observaciones="Gasto de prueba"
    )
    
    # Recargar la caja para ver el saldo actualizado
    caja.refresh_from_db()
    print(f"Después de gasto (-30): {caja.saldo}")
    assert caja.saldo == Decimal('70.00'), f"Esperado 70.00, obtenido {caja.saldo}"
    
    # Eliminar el movimiento de gasto (debe volver el saldo a 100)
    movimiento_gasto.delete()
    
    # Recargar la caja para ver el saldo actualizado
    caja.refresh_from_db()
    print(f"Después de eliminar gasto (+30): {caja.saldo}")
    assert caja.saldo == Decimal('100.00'), f"Esperado 100.00, obtenido {caja.saldo}"
    
    # Eliminar el movimiento de ingreso (debe volver el saldo a 0)
    movimiento_ingreso.delete()
    
    # Recargar la caja para ver el saldo actualizado
    caja.refresh_from_db()
    print(f"Después de eliminar ingreso (-100): {caja.saldo}")
    assert caja.saldo == Decimal('0.00'), f"Esperado 0.00, obtenido {caja.saldo}"
    
    print("\n✅ TODAS LAS PRUEBAS PASARON")
    print("Las señales Django están funcionando correctamente")
    
    # Limpiar datos de prueba
    caja.delete()
    turno.delete()
    concepto_ingreso.delete()
    concepto_gasto.delete()


if __name__ == "__main__":
    test_saldo_updates()
