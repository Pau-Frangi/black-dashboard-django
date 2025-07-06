#!/usr/bin/env python
"""
Script de prueba para verificar que las señales del desglose funcionan correctamente
cuando se crean, modifican o eliminan desgloses desde el admin.
"""

import os
import django
from decimal import Decimal

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.dyn_dt.models import Caja, DenominacionEuro, DesgloseCaja


def test_desglose_admin_signals():
    """Prueba que las señales del desglose actualicen el saldo correctamente"""
    
    print("=== PRUEBA DE SEÑALES DEL DESGLOSE ===\n")
    
    # Crear una caja de prueba
    print("1. Creando caja de prueba...")
    caja = Caja.objects.create(
        nombre="Caja Desglose Test",
        año=2025,
        saldo=Decimal('0.00'),
        activa=True
    )
    print(f"   ✅ Caja creada con saldo inicial: {caja.saldo}€")
    
    # Crear algunas denominaciones de prueba si no existen
    print("\n2. Verificando denominaciones...")
    denom_50, created = DenominacionEuro.objects.get_or_create(
        valor=Decimal('50.00'),
        defaults={'es_billete': True, 'activa': True}
    )
    
    denom_20, created = DenominacionEuro.objects.get_or_create(
        valor=Decimal('20.00'),
        defaults={'es_billete': True, 'activa': True}
    )
    
    denom_2, created = DenominacionEuro.objects.get_or_create(
        valor=Decimal('2.00'),
        defaults={'es_billete': False, 'activa': True}
    )
    
    print("   ✅ Denominaciones verificadas")
    
    # Verificar saldo inicial después de inicialización
    caja.refresh_from_db()
    print(f"   Saldo después de inicialización: {caja.saldo}€")
    
    # PRUEBA 1: Modificar desglose existente (debe actualizar saldo)
    print("\n3. Modificando desglose: 2 billetes de 50€...")
    desglose_50, created = DesgloseCaja.objects.get_or_create(
        caja=caja,
        denominacion=denom_50,
        defaults={'cantidad': 0}
    )
    desglose_50.cantidad = 2
    desglose_50.save()
    
    caja.refresh_from_db()
    print(f"   Saldo después de establecer 2x50€: {caja.saldo}€ (esperado: 100.00€)")
    assert caja.saldo == Decimal('100.00'), f"Esperado 100.00, obtenido {caja.saldo}"
    
    # PRUEBA 2: Modificar más desglose
    print("\n4. Modificando desglose: 1 billete de 20€...")
    desglose_20, created = DesgloseCaja.objects.get_or_create(
        caja=caja,
        denominacion=denom_20,
        defaults={'cantidad': 0}
    )
    desglose_20.cantidad = 1
    desglose_20.save()
    
    caja.refresh_from_db()
    print(f"   Saldo después de establecer 1x20€: {caja.saldo}€ (esperado: 120.00€)")
    assert caja.saldo == Decimal('120.00'), f"Esperado 120.00, obtenido {caja.saldo}"
    
    # PRUEBA 3: Modificar desglose existente
    print("\n5. Modificando desglose: cambiar 2 billetes de 50€ a 3...")
    desglose_50.cantidad = 3
    desglose_50.save()
    
    caja.refresh_from_db()
    print(f"   Saldo después de cambiar a 3x50€: {caja.saldo}€ (esperado: 170.00€)")
    assert caja.saldo == Decimal('170.00'), f"Esperado 170.00, obtenido {caja.saldo}"
    
    # PRUEBA 4: Añadir monedas
    print("\n6. Modificando desglose: 5 monedas de 2€...")
    desglose_2, created = DesgloseCaja.objects.get_or_create(
        caja=caja,
        denominacion=denom_2,
        defaults={'cantidad': 0}
    )
    desglose_2.cantidad = 5
    desglose_2.save()
    
    caja.refresh_from_db()
    print(f"   Saldo después de establecer 5x2€: {caja.saldo}€ (esperado: 180.00€)")
    assert caja.saldo == Decimal('180.00'), f"Esperado 180.00, obtenido {caja.saldo}"
    
    # PRUEBA 5: Eliminar un desglose (reducir a 0)
    print("\n7. Reduciendo desglose de billetes de 20€ a 0...")
    desglose_20.cantidad = 0
    desglose_20.save()
    
    caja.refresh_from_db()
    print(f"   Saldo después de reducir 20€ a 0: {caja.saldo}€ (esperado: 160.00€)")
    assert caja.saldo == Decimal('160.00'), f"Esperado 160.00, obtenido {caja.saldo}"
    
    # PRUEBA 6: Eliminar físicamente un desglose
    print("\n8. Eliminando físicamente el desglose de monedas de 2€...")
    desglose_2.delete()
    
    caja.refresh_from_db()
    print(f"   Saldo después de eliminar el desglose: {caja.saldo}€ (esperado: 150.00€)")
    assert caja.saldo == Decimal('150.00'), f"Esperado 150.00, obtenido {caja.saldo}"
    
    # PRUEBA 7: Verificar método calcular_saldo_desde_desglose
    print("\n9. Verificando método calcular_saldo_desde_desglose...")
    saldo_calculado = caja.calcular_saldo_desde_desglose()
    print(f"   Saldo calculado desde desglose: {saldo_calculado}€")
    print(f"   Saldo actual en BD: {caja.saldo}€")
    assert saldo_calculado == caja.saldo, f"Saldos no coinciden: {saldo_calculado} vs {caja.saldo}"
    
    print("\n✅ TODAS LAS PRUEBAS DEL DESGLOSE PASARON")
    print("Las señales Django actualizan correctamente el saldo cuando se modifica el desglose")
    
    # Mostrar desglose final
    print(f"\n📊 DESGLOSE FINAL DE {caja.nombre}:")
    for desglose in caja.obtener_desglose_actual():
        if desglose.cantidad > 0:
            tipo = "billete" if desglose.denominacion.es_billete else "moneda"
            print(f"   {desglose.cantidad}x {desglose.denominacion.valor}€ ({tipo}) = {desglose.valor_total()}€")
    print(f"   TOTAL: {caja.saldo}€")
    
    # Limpiar datos de prueba
    print("\n🧹 Limpiando datos de prueba...")
    caja.delete()
    
    # Solo eliminar denominaciones si las creamos nosotros
    # (en un entorno real probablemente ya existan)
    
    print("✅ Limpieza completada")


if __name__ == "__main__":
    test_desglose_admin_signals()
