"""
Movement handling using Django forms for better validation and organization
"""
from django.http import JsonResponse
from django.contrib.contenttypes.models import ContentType
from pydantic import ValidationError
from apps.caja.models import MovimientoCajaIngreso, MovimientoCajaGasto, MovimientoEfectivo, DesgloseCaja
from apps.banco.models import MovimientoBancoIngreso, MovimientoBancoGasto
from apps.caja.forms import MovimientoCajaIngresoForm, MovimientoCajaGastoForm, DesgloseCajaForm
from apps.banco.forms import MovimientoBancoIngresoForm, MovimientoBancoGastoForm
from apps.dyn_dt.models import Concepto
import traceback


class MovementHandler:
    """Handler for movement operations using Django forms"""
    
    @staticmethod
    def create_movement(request):
        """Create a new movement using appropriate form based on type and concept"""
        try:
            canal_movimiento = request.POST.get('canal_movimiento')
            concepto_id = request.POST.get('concepto_id') or request.POST.get('concepto')
            
            print(f"DEBUG: canal_movimiento={canal_movimiento}, concepto_id={concepto_id}")
            print(f"DEBUG: All POST data: {dict(request.POST)}")
            
            if not canal_movimiento or not concepto_id:
                return JsonResponse({
                    'success': False, 
                    'error': 'Canal de movimiento y concepto son requeridos'
                })
            
            # Get concepto to determine if it's gasto or ingreso
            try:
                concepto = Concepto.objects.get(id=concepto_id)
            except Concepto.DoesNotExist:
                return JsonResponse({
                    'success': False, 
                    'error': 'Concepto no encontrado'
                })
            
            es_gasto = concepto.es_gasto
            
            # Create a mutable copy of POST data to fix field names
            post_data = request.POST.copy()
            
            # Fix field names for Django forms
            post_data['concepto'] = concepto_id
            if 'concepto_id' in post_data:
                del post_data['concepto_id']
            
            # Ensure ejercicio and campamento are properly set
            if 'ejercicio_id' in post_data:
                post_data['ejercicio'] = post_data['ejercicio_id']
            if 'campamento_id' in post_data:
                post_data['campamento'] = post_data['campamento_id']
            
            print(f"DEBUG: Fixed POST data: {dict(post_data)}")
            
            # Select appropriate form based on canal_movimiento and es_gasto
            # Pass user to form constructor
            if canal_movimiento == 'caja':
                if es_gasto:
                    form = MovimientoCajaGastoForm(post_data, request.FILES, user=request.user)
                    # Add justificante field handling for cash expenses
                    justificante = request.POST.get('justificante', '')
                else:
                    form = MovimientoCajaIngresoForm(post_data, request.FILES, user=request.user)
                    justificante = None
            elif canal_movimiento == 'banco':
                if es_gasto:
                    form = MovimientoBancoGastoForm(post_data, request.FILES, user=request.user)
                else:
                    form = MovimientoBancoIngresoForm(post_data, request.FILES, user=request.user)
                justificante = None
            else:
                return JsonResponse({
                    'success': False, 
                    'error': 'Canal de movimiento no válido'
                })
            
            print(f"DEBUG: Form errors: {form.errors}")
            
            if form.is_valid():
                # Create the movement instance - user tracking is handled by form
                movement = form.save(commit=False)
                
                # Handle justificante for cash expenses
                if canal_movimiento == 'caja' and es_gasto and justificante:
                    # Since justificante is not a model field, we need to handle it differently
                    # For now, we'll add it to the description
                    if justificante:
                        movement.descripcion += f" [Justificante: {justificante}]"
                
                # Save the movement (user tracking is handled by form)
                movement.save()
                
                # Handle money breakdown for cash movements
                if canal_movimiento == 'caja':
                    MovementHandler._handle_money_breakdown(request, movement)
                
                return JsonResponse({
                    'success': True,
                    'message': f'Movimiento de {canal_movimiento} {"gasto" if es_gasto else "ingreso"} creado correctamente',
                    'movement_id': movement.id
                })
            else:
                # Return form errors
                errors = []
                for field, field_errors in form.errors.items():
                    for error in field_errors:
                        errors.append(f"{field}: {error}")
                
                return JsonResponse({
                    'success': False,
                    'error': 'Errores de validación: ' + '; '.join(errors)
                })
                
        except Exception as e:
            print(f"Error creating movement: {e}")
            print(traceback.format_exc())
            return JsonResponse({
                'success': False,
                'error': f'Error interno del servidor: {str(e)}'
            })

    @staticmethod
    def _handle_money_breakdown(request, movement):
        """Handle money breakdown for cash movements"""
        try:
            # Get all denomination entries from POST data
            for key, value in request.POST.items():
                if key.startswith('entrada_') or key.startswith('salida_'):
                    parts = key.split('_')
                    if len(parts) == 2:
                        tipo = parts[0]  # 'entrada' or 'salida'
                        denominacion_id = parts[1]
                        cantidad = int(value) if value else 0
                        
                        if cantidad > 0:
                            # Get or create MovimientoEfectivo
                            content_type = ContentType.objects.get_for_model(movement)
                            
                            movimiento_efectivo, created = MovimientoEfectivo.objects.get_or_create(
                                content_type=content_type,
                                object_id=movement.id,
                                caja=movement.caja,
                                denominacion_id=denominacion_id,
                                defaults={'creado_por': request.user}
                            )
                            
                            if tipo == 'entrada':
                                movimiento_efectivo.cantidad_entrada = cantidad
                            elif tipo == 'salida':
                                movimiento_efectivo.cantidad_salida = cantidad
                            
                            movimiento_efectivo.save()
                            
        except Exception as e:
            print(f"Error handling money breakdown: {e}")
            print(traceback.format_exc())
    
    @staticmethod
    def edit_movement(request):
        """Edit an existing movement"""
        try:
            movimiento_id = request.POST.get('movimiento_id')
            tipo_movimiento = request.POST.get('tipo_movimiento')
            
            if not movimiento_id or not tipo_movimiento:
                return JsonResponse({
                    'success': False, 
                    'error': 'ID del movimiento y tipo son requeridos'
                })
            
            # Find the movement based on type
            movement = None
            form = None
            
            # Create a mutable copy of POST data to fix field names
            post_data = request.POST.copy()
            
            # Ensure concepto is properly set from concepto_id if needed
            concepto_id = post_data.get('concepto_id') or post_data.get('concepto')
            if concepto_id:
                post_data['concepto'] = concepto_id
            
            # Ensure ejercicio and campamento are properly set
            if 'ejercicio_id' in post_data:
                post_data['ejercicio'] = post_data['ejercicio_id']
            if 'campamento_id' in post_data:
                post_data['campamento'] = post_data['campamento_id']
            
            print(f"DEBUG: Edit POST data: {dict(post_data)}")
            
            if tipo_movimiento == 'caja':
                # Try to find in both ingreso and gasto models
                try:
                    movement = MovimientoCajaIngreso.objects.get(id=movimiento_id)
                    form = MovimientoCajaIngresoForm(post_data, request.FILES, instance=movement, user=request.user)
                except MovimientoCajaIngreso.DoesNotExist:
                    try:
                        movement = MovimientoCajaGasto.objects.get(id=movimiento_id)
                        form = MovimientoCajaGastoForm(post_data, request.FILES, instance=movement, user=request.user)
                    except MovimientoCajaGasto.DoesNotExist:
                        pass
            elif tipo_movimiento == 'banco':
                # Try to find in both ingreso and gasto models
                try:
                    movement = MovimientoBancoIngreso.objects.get(id=movimiento_id)
                    form = MovimientoBancoIngresoForm(post_data, request.FILES, instance=movement, user=request.user)
                except MovimientoBancoIngreso.DoesNotExist:
                    try:
                        movement = MovimientoBancoGasto.objects.get(id=movimiento_id)
                        form = MovimientoBancoGastoForm(post_data, request.FILES, instance=movement, user=request.user)
                    except MovimientoBancoGasto.DoesNotExist:
                        pass
            
            if not movement or not form:
                return JsonResponse({
                    'success': False, 
                    'error': 'Movimiento no encontrado'
                })
            
            print(f"DEBUG: Form errors: {form.errors}")
            
            if form.is_valid():
                # Update the movement - user tracking is handled by form
                updated_movement = form.save()
                
                # Handle money breakdown for cash movements
                if tipo_movimiento == 'caja':
                    # Clear existing money breakdown
                    content_type = ContentType.objects.get_for_model(movement)
                    MovimientoEfectivo.objects.filter(
                        content_type=content_type,
                        object_id=movement.id
                    ).delete()
                    
                    # Create new breakdown
                    MovementHandler._handle_money_breakdown(request, updated_movement)
                
                return JsonResponse({
                    'success': True,
                    'message': 'Movimiento actualizado correctamente'
                })
            else:
                # Return form errors
                errors = []
                for field, field_errors in form.errors.items():
                    for error in field_errors:
                        errors.append(f"{field}: {error}")
                
                return JsonResponse({
                    'success': False,
                    'error': 'Errores de validación: ' + '; '.join(errors)
                })
                
        except Exception as e:
            print(f"Error editing movement: {e}")
            print(traceback.format_exc())
            return JsonResponse({
                'success': False,
                'error': f'Error interno del servidor: {str(e)}'
            })
    
    @staticmethod
    def delete_movement(request):
        """Delete a movement"""
        try:
            movimiento_id = request.POST.get('movimiento_id')
            tipo_movimiento = request.POST.get('tipo_movimiento')
            
            if not movimiento_id or not tipo_movimiento:
                return JsonResponse({
                    'success': False, 
                    'error': 'ID del movimiento y tipo son requeridos'
                })
            
            # Find and delete the movement
            movement = None
            
            if tipo_movimiento == 'caja':
                # Try to find in both ingreso and gasto models
                try:
                    movement = MovimientoCajaIngreso.objects.get(id=movimiento_id)
                except MovimientoCajaIngreso.DoesNotExist:
                    try:
                        movement = MovimientoCajaGasto.objects.get(id=movimiento_id)
                    except MovimientoCajaGasto.DoesNotExist:
                        pass
            elif tipo_movimiento == 'banco':
                # Try to find in both ingreso and gasto models
                try:
                    movement = MovimientoBancoIngreso.objects.get(id=movimiento_id)
                except MovimientoBancoIngreso.DoesNotExist:
                    try:
                        movement = MovimientoBancoGasto.objects.get(id=movimiento_id)
                    except MovimientoBancoGasto.DoesNotExist:
                        pass
            
            if not movement:
                return JsonResponse({
                    'success': False, 
                    'error': 'Movimiento no encontrado'
                })
            
            # Delete the movement (related MovimientoEfectivo will be deleted by signals)
            movement.delete()
            
            return JsonResponse({
                'success': True,
                'message': 'Movimiento eliminado correctamente'
            })
            
        except Exception as e:
            print(f"Error deleting movement: {e}")
            print(traceback.format_exc())
            return JsonResponse({
                'success': False,
                'error': f'Error interno del servidor: {str(e)}'
            })
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
        desglose_form = DesgloseCajaForm(request.POST)
        if desglose_form.is_valid():
            movimientos_dinero_data = desglose_form.get_movimientos_dinero_data()
            content_type = ContentType.objects.get_for_model(movimiento)
            for mov_data in movimientos_dinero_data:
                MovimientoEfectivo.objects.create(
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
        movimiento.caja.recalcular_saldo_caja()
        raise ValidationError('El desglose de dinero es inválido o está incompleto')

