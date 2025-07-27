"""
Handlers for movement creation, editing, and deletion operations.
"""
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.core.exceptions import ValidationError
from decimal import Decimal

from apps.dyn_dt.models import (
    Caja, Concepto, MovimientoCaja, MovimientoBanco, 
    MovimientoDinero, DesgloseCaja, Ejercicio, Turno, Campamento, CuentaBancaria, ViaMovimientoBanco
)
from apps.dyn_dt.forms import DesgloseDineroForm
from apps.dyn_dt.utils import combine_date_time
from django.contrib.contenttypes.models import ContentType



class MovementHandler:
    """Handles movement creation, editing, and deletion."""
    
    @staticmethod
    def create_movement(request):
        """
        Creates a new movement (cash or bank).
        
        Args:
            request: Django request object with movement data
            
        Returns:
            JsonResponse indicating success or failure
        """
        try:
            
            # Get operation type and validate
            tipo_operacion = request.POST.get('tipo_operacion')
            if not tipo_operacion or tipo_operacion not in ['efectivo', 'transferencia']:
                return JsonResponse({
                    'success': False, 
                    'error': 'Tipo de operación inválido'
                })
            
            # Parse common data
            fecha_datetime = combine_date_time(
                request.POST.get('fecha'), 
                request.POST.get('hora', '12:00')
            )
            turno = get_object_or_404(Turno, id=request.POST.get('turno_id'))
            concepto = get_object_or_404(Concepto, id=request.POST.get('concepto_id'))
            cantidad_decimal = Decimal(str(request.POST.get('cantidad')))
            ejercicio = get_object_or_404(Ejercicio, id=request.POST.get('ejercicio_id'))
            campamento = get_object_or_404(Campamento, id=request.POST.get('campamento_id'))

            
            # Create movement based on type
            if tipo_operacion == 'transferencia':
                cuenta_bancaria = get_object_or_404(CuentaBancaria, id=request.POST.get('cuenta_bancaria_id'))
                via_movimiento_bancario = ViaMovimientoBanco.objects.get(id=request.POST.get('via_movimiento_bancario_id'))
                movimiento = MovementCreator.create_bank_movement(
                    request, campamento, ejercicio, turno, concepto, cuenta_bancaria, via_movimiento_bancario, cantidad_decimal, fecha_datetime
                )
            else:
                caja = get_object_or_404(Caja, id=request.POST.get('caja_id'))

                # Validate caja is active
                if not caja.activa:
                    return JsonResponse({
                        'success': False, 
                        'error': 'No se pueden añadir movimientos a una caja inactiva'
                    })
                    
                movimiento = MovementCreator.create_cash_movement(
                    request, ejercicio, caja, turno, concepto, cantidad_decimal, fecha_datetime
                )
            
            # Set user before saving
            movimiento.save(user=request.user)  # Pass user explicitly
            
            # Process money breakdown if needed (to create the MovimientoDinero)
            if tipo_operacion == 'efectivo':
                MovementCreator.process_money_breakdown(request, movimiento)
            
            return JsonResponse({
                'success': True, 
                'message': 'Movimiento añadido correctamente'
            })
            
        except Exception as e:
            return JsonResponse({'success': False, 'error': 'algo va mal: ' + str(e)})
    
    @staticmethod
    def delete_movement(request):
        """
        Deletes a movement.
        
        Args:
            request: Django request object with movement ID and type
            
        Returns:
            JsonResponse indicating success or failure
        """
        try:
            movimiento_id = request.POST.get('movimiento_id')
            tipo_movimiento = request.POST.get('tipo_movimiento', 'caja')
            
            if tipo_movimiento == 'banco':
                movimiento = get_object_or_404(MovimientoBanco, id=movimiento_id)
            else:
                movimiento = get_object_or_404(MovimientoCaja, id=movimiento_id)
            
            movimiento.delete()
            return JsonResponse({
                'success': True, 
                'message': 'Movimiento eliminado correctamente'
            })
            
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    @staticmethod
    def edit_movement(request):
        """
        Handles movement editing logic.
        
        Args:
            request: Django request object with updated movement data
            
        Returns:
            JsonResponse indicating success or failure
        """
        try:
            movimiento_id = request.POST.get('movimiento_id')
            tipo_movimiento = request.POST.get('tipo_movimiento', 'caja')
            
            # Get the existing movement
            if tipo_movimiento == 'banco':
                movimiento = get_object_or_404(MovimientoBanco, id=movimiento_id)
            else:
                movimiento = get_object_or_404(MovimientoCaja, id=movimiento_id)
            
            # Store original values for saldo calculation
            cantidad_original = movimiento.cantidad
            
            # Update basic fields
            fecha_datetime = combine_date_time(
                request.POST.get('fecha'),
                request.POST.get('hora', '12:00')
            )
            cantidad_decimal = Decimal(str(request.POST.get('cantidad')))
            
            # Update common fields
            movimiento.cantidad = cantidad_decimal
            movimiento.fecha = fecha_datetime
            movimiento.descripcion = request.POST.get('descripcion') or None
            
            # Update type-specific fields
            if tipo_movimiento == 'banco':
                MovementUpdater.update_bank_movement_fields(request, movimiento)
            else:
                MovementUpdater.update_cash_movement_fields(request, movimiento)
            
            # Validate and save
            movimiento.full_clean()
            movimiento.save()
            
            # Update saldos
            MovementUpdater.update_saldos_after_edit(
                movimiento, cantidad_original, tipo_movimiento, request
            )
            
            return JsonResponse({
                'success': True, 
                'message': 'Movimiento actualizado correctamente'
            })
            
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})


class MovementCreator:
    """Helper class for creating movements."""
    
    @staticmethod
    def create_bank_movement(request, campamento, ejercicio, turno, concepto, cuenta_bancaria, via_movimiento_bancario, cantidad_decimal, fecha_datetime):
        """Creates a bank movement"""

        return MovimientoBanco(
            campamento=campamento,
            ejercicio=ejercicio,
            turno=turno,
            concepto=concepto,
            cantidad=cantidad_decimal,
            fecha=fecha_datetime,
            descripcion=request.POST.get('descripcion') or None,
            cuenta_bancaria=cuenta_bancaria,
            via = via_movimiento_bancario,
            referencia_bancaria=request.POST.get('referencia_bancaria'),
            archivo_justificante=request.FILES.get('archivo_justificante_banco'),
        )
    
    @staticmethod
    def create_cash_movement(request, ejercicio, caja, turno, concepto, cantidad, fecha):
        """
        Creates a cash movement.
        
        Args:
            request: Django request object
            caja: Caja instance
            concepto: Concepto instance
            cantidad: Movement amount
            fecha: Movement datetime
            
        Returns:
            MovimientoCaja instance
        """
        movimiento = MovimientoCaja(
            ejercicio=ejercicio,
            caja=caja,
            turno=turno,
            concepto=concepto,
            cantidad=cantidad,
            fecha=fecha,
            descripcion=request.POST.get('descripcion') or None
        )
        
        # Handle justificante fields (only for gastos)
        if concepto.es_gasto:
            movimiento.justificante = request.POST.get('justificante') or None
            if 'archivo_justificante' in request.FILES:
                movimiento.archivo_justificante = request.FILES['archivo_justificante']
        else:
            movimiento.justificante = None
            movimiento.archivo_justificante = None
        
        return movimiento
    
    @staticmethod
    def process_money_breakdown(request, movimiento):
        """
        Processes money breakdown for cash movements.
        """
        desglose_form = DesgloseDineroForm(request.POST)
        if desglose_form.is_valid():
            movimientos_dinero_data = desglose_form.get_movimientos_dinero_data()
            content_type = ContentType.objects.get_for_model(movimiento)
            for mov_data in movimientos_dinero_data:
                MovimientoDinero.objects.create(
                    content_type=content_type,
                    object_id=movimiento.id,
                    denominacion=mov_data['denominacion'],
                    cantidad_entrada=mov_data['cantidad_entrada'],
                    cantidad_salida=mov_data['cantidad_salida'],
                    creado_por=request.user
                )


class MovementUpdater:
    """Helper class for updating movements."""
    
    @staticmethod
    def update_bank_movement_fields(request, movimiento):
        """
        Updates bank-specific movement fields.
        
        Args:
            request: Django request object
            movimiento: MovimientoBanco instance
        """
        movimiento.referencia_bancaria = request.POST.get('referencia_bancaria') or None
        
        if 'archivo_justificante_banco' in request.FILES:
            if movimiento.archivo_justificante:
                movimiento.archivo_justificante.delete()
            movimiento.archivo_justificante = request.FILES['archivo_justificante_banco']
    
    @staticmethod
    def update_cash_movement_fields(request, movimiento):
        """
        Updates cash-specific movement fields.
        
        Args:
            request: Django request object
            movimiento: MovimientoCaja instance
        """
        movimiento.turno_id = request.POST.get('turno')
        
        if movimiento.concepto.es_gasto:
            movimiento.justificante = request.POST.get('justificante') or None
            
            if 'archivo_justificante' in request.FILES:
                if movimiento.archivo_justificante:
                    movimiento.archivo_justificante.delete()
                movimiento.archivo_justificante = request.FILES['archivo_justificante']
        else:
            movimiento.justificante = None
            if movimiento.archivo_justificante:
                movimiento.archivo_justificante.delete()
                movimiento.archivo_justificante = None
    
    @staticmethod
    def update_saldos_after_edit(movimiento, cantidad_original, tipo_movimiento, request):
        """
        Updates saldos after movement edit.
        
        Args:
            movimiento: Movement instance
            cantidad_original: Original movement amount
            tipo_movimiento: Type of movement ('caja' or 'banco')
            request: Django request object
        """
        if tipo_movimiento == 'banco':
            MovementUpdater._update_bank_saldo(movimiento, cantidad_original)
        else:
            MovementUpdater._update_cash_movement_breakdown(movimiento, request)
    
    @staticmethod
    def _update_bank_saldo(movimiento, cantidad_original):
        """Updates bank saldo calculation."""
        cantidad_real_original = -cantidad_original if movimiento.es_gasto() else cantidad_original
        cantidad_real_nueva = movimiento.cantidad_real()
        diferencia = cantidad_real_nueva - cantidad_real_original
        
        ejercicio = movimiento.ejercicio
        ejercicio.saldo_banco += diferencia
        ejercicio.save()
    
    @staticmethod
    def _update_cash_movement_breakdown(movimiento, request):
        """Updates cash movement money breakdown."""
        # Revert original money breakdown
        for mov_dinero in movimiento.movimientos_dinero.all():
            desglose = DesgloseCaja.objects.filter(
                caja=movimiento.caja,
                denominacion=mov_dinero.denominacion
            ).first()
            
            if desglose:
                desglose.cantidad -= mov_dinero.cantidad_neta()
                if desglose.cantidad < 0:
                    desglose.cantidad = 0
                desglose.save()
        
        # Delete existing MovimientoDinero records
        movimiento.movimientos_dinero.all().delete()
        
        # Create new MovimientoDinero records
        desglose_form = DesgloseDineroForm(request.POST)
        if desglose_form.is_valid():
            movimientos_dinero_data = desglose_form.get_movimientos_dinero_data()
            content_type = ContentType.objects.get_for_model(movimiento)
            for mov_data in movimientos_dinero_data:
                MovimientoDinero.objects.create(
                    content_type=content_type,
                    object_id=movimiento.id,
                    denominacion=mov_data['denominacion'],
                    cantidad_entrada=mov_data['cantidad_entrada'],
                    cantidad_salida=mov_data['cantidad_salida'],
                    creado_por=request.user
                )
        else:
            raise ValidationError('El desglose de dinero es inválido o está incompleto')
        
        # Recalculate caja saldo
        movimiento.caja.recalcular_saldo_caja()
        movimiento.caja.recalcular_saldo_caja()
        raise ValidationError('El desglose de dinero es inválido o está incompleto')
        
