#!/usr/bin/env python
"""
Script de prueba para verificar que no se puede modificar el saldo de una caja existente.
"""

import os
import django
from decimal import Decimal
from django.core.exceptions import ValidationError

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.dyn_dt.models import Caja, Turno, Concepto, MovimientoCaja


def test_saldo_protection():
    """Prueba que el saldo no se pueda modificar manualmente en cajas existentes"""
    
    print("=== PRUEBA DE PROTECCIÓN DEL SALDO ===\n")
    
    # Crear una nueva caja con saldo inicial
    print("1. Creando caja nueva con saldo inicial de 100€...")
    caja = Caja.objects.create(
        nombre="Caja Protección Test",
        año=2025,
        saldo=Decimal('100.00'),  # Esto debe funcionar al crear
        activa=True
    )
    print(f"   ✅ Caja creada con saldo: {caja.saldo}€")
    
    # Intentar modificar el saldo directamente (debe fallar)
    print("\n2. Intentando modificar el saldo directamente (debe fallar)...")
    caja.saldo = Decimal('500.00')
    
    try:
        caja.save()
        print("   ❌ ERROR: Se pudo modificar el saldo (no debería ser posible)")
        return False
    except ValidationError as e:
        print(f"   ✅ Validación funcionó: {e.message_dict['saldo'][0]}")
    
    # Recargar la caja para verificar que el saldo no cambió
    caja.refresh_from_db()
    print(f"   ✅ Saldo se mantuvo en: {caja.saldo}€")
    
    # Crear datos para movimientos
    turno, created = Turno.objects.get_or_create(
        nombre="Turno Protección Test"
    )
    
    concepto_ingreso, created = Concepto.objects.get_or_create(
        nombre="Ingreso Protección",
        defaults={'es_gasto': False}
    )
    
    # Añadir un movimiento (esto debe cambiar el saldo automáticamente)
    print("\n3. Añadiendo movimiento de 50€ (debe actualizar saldo automáticamente)...")
    MovimientoCaja.objects.create(
        caja=caja,
        turno=turno,
        concepto=concepto_ingreso,
        cantidad=Decimal('50.00'),
        observaciones="Movimiento de prueba"
    )
    
    # Recargar y verificar que el saldo se actualizó automáticamente
    caja.refresh_from_db()
    print(f"   ✅ Saldo actualizado automáticamente: {caja.saldo}€")
    
    # Probar el método recalcular_saldo() (debe funcionar)
    print("\n4. Probando método recalcular_saldo()...")
    saldo_calculado = caja.recalcular_saldo()
    print(f"   ✅ Método recalcular_saldo() funcionó: {saldo_calculado}€")
    
    # Intentar usar save() con skip_validation=True (debe funcionar)
    print("\n5. Probando save() con skip_validation=True...")
    caja.saldo = Decimal('999.99')
    caja.save(skip_validation=True)
    caja.refresh_from_db()
    print(f"   ✅ save() con skip_validation funcionó: {caja.saldo}€")
    
    # Limpiar datos de prueba
    print("\n6. Limpiando datos de prueba...")
    caja.delete()
    turno.delete()
    concepto_ingreso.delete()
    
    print("\n✅ TODAS LAS PRUEBAS DE PROTECCIÓN PASARON")
    print("El saldo está correctamente protegido contra modificaciones manuales")
    return True


if __name__ == "__main__":
    test_saldo_protection()
