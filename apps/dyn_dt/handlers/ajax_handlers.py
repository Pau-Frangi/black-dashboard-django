"""
AJAX request handlers for the registro application
"""
from django.http import JsonResponse
from apps.caja.models import Caja, DesgloseCaja, MovimientoEfectivo
from apps.banco.models import CuentaBancaria, ViaMovimientoBanco
from apps.dyn_dt.models import Turno, Ejercicio, Campamento
from django.contrib.contenttypes.models import ContentType


class RegistroAjaxHandler:
    """Handler for new ejercicio-based AJAX requests"""
    
    @staticmethod
    def handle_get_ejercicio_movimientos(request):
        """Handle ejercicio movements request"""
        ejercicio_id = request.GET.get('ejercicio_id')
        campamento_id = request.GET.get('campamento_id')
        
        if not ejercicio_id or not campamento_id:
            return JsonResponse({
                'success': False,
                'error': 'Ejercicio ID y Campamento ID son requeridos'
            })
        
        try:
            from apps.caja.models import MovimientoCajaIngreso, MovimientoCajaGasto
            from apps.banco.models import MovimientoBancoIngreso, MovimientoBancoGasto
            
            ejercicio = Ejercicio.objects.get(id=ejercicio_id)
            campamento = Campamento.objects.get(id=campamento_id)
            
            # Get all movements for this ejercicio and campamento
            movimientos_caja_ingreso = MovimientoCajaIngreso.objects.filter(
                ejercicio=ejercicio, 
                caja__campamento=campamento
            ).select_related('caja', 'turno', 'concepto')
            
            movimientos_caja_gasto = MovimientoCajaGasto.objects.filter(
                ejercicio=ejercicio, 
                caja__campamento=campamento
            ).select_related('caja', 'turno', 'concepto')
            
            movimientos_banco_ingreso = MovimientoBancoIngreso.objects.filter(
                ejercicio=ejercicio,
                campamento=campamento
            ).select_related('cuenta_bancaria', 'via', 'turno', 'concepto')
            
            movimientos_banco_gasto = MovimientoBancoGasto.objects.filter(
                ejercicio=ejercicio,
                campamento=campamento
            ).select_related('cuenta_bancaria', 'turno', 'concepto')
            
            # Serialize all movements
            all_movimientos = []
            
            # Add cash movements
            for mov in movimientos_caja_ingreso:
                data = mov.serializar()
                data['tipo'] = 'caja'
                data['es_gasto'] = False
                all_movimientos.append(data)
                
            for mov in movimientos_caja_gasto:
                data = mov.serializar()
                data['tipo'] = 'caja'
                data['es_gasto'] = True
                all_movimientos.append(data)
            
            # Add bank movements
            for mov in movimientos_banco_ingreso:
                data = mov.serializar()
                data['tipo'] = 'banco'
                data['es_gasto'] = False
                all_movimientos.append(data)
                
            for mov in movimientos_banco_gasto:
                data = mov.serializar()
                data['tipo'] = 'banco'
                data['es_gasto'] = True
                all_movimientos.append(data)
            
            # Calculate totals
            total_ingresos = sum(mov['importe'] for mov in all_movimientos if not mov['es_gasto'])
            total_gastos = sum(mov['importe'] for mov in all_movimientos if mov['es_gasto'])
            saldo_actual = total_ingresos - total_gastos
            
            resumen = {
                'total_ingresos': float(total_ingresos),
                'total_gastos': float(total_gastos),
                'saldo_actual': float(saldo_actual)
            }
            
            return JsonResponse({
                'success': True,
                'ejercicio': {
                    'id': ejercicio.id,
                    'nombre': ejercicio.nombre,
                    'año': ejercicio.año
                },
                'movimientos': all_movimientos,
                'resumen': resumen
            })
            
        except (Ejercicio.DoesNotExist, Campamento.DoesNotExist):
            return JsonResponse({
                'success': False,
                'error': 'Ejercicio o Campamento no encontrado'
            })
        except Exception as e:
            print(f"Error in handle_get_ejercicio_movimientos: {e}")
            import traceback
            traceback.print_exc()
            return JsonResponse({
                'success': False,
                'error': f'Error interno: {str(e)}'
            })
    
    @staticmethod
    def handle_get_turnos(request):
        """Handle turnos request for a specific ejercicio"""
        ejercicio_id = request.GET.get('ejercicio_id')
        campamento_id = request.GET.get('campamento_id')
        
        if not ejercicio_id or not campamento_id:
            return JsonResponse({
                'success': False,
                'error': 'Ejercicio ID y Campamento ID son requeridos'
            })
        
        try:
            ejercicio = Ejercicio.objects.get(id=ejercicio_id)
            campamento = Campamento.objects.get(id=campamento_id)
            
            # Get turnos for this ejercicio and campamento
            turnos = ejercicio.turnos.filter(campamento=campamento).order_by('nombre')
            
            turnos_data = [{
                'id': turno.id,
                'nombre': turno.nombre
            } for turno in turnos]
            
            return JsonResponse({
                'success': True,
                'turnos': turnos_data
            })
            
        except (Ejercicio.DoesNotExist, Campamento.DoesNotExist):
            return JsonResponse({
                'success': False,
                'error': 'Ejercicio o Campamento no encontrado'
            })
        except Exception as e:
            print(f"Error in handle_get_turnos: {e}")
            return JsonResponse({
                'success': False,
                'error': f'Error interno: {str(e)}'
            })
    
    @staticmethod
    def handle_get_cajas(request):
        """Handle cajas request for a specific campamento"""
        campamento_id = request.GET.get('campamento_id')
        
        if not campamento_id:
            return JsonResponse({
                'success': False,
                'error': 'Campamento ID es requerido'
            })
        
        try:
            campamento = Campamento.objects.get(id=campamento_id)
            
            # Get cajas for this campamento
            cajas = Caja.objects.filter(campamento=campamento).order_by('nombre')
            
            cajas_data = [{
                'id': caja.id,
                'nombre': caja.nombre,
                'activa': caja.activa,
                'saldo_caja': float(caja.saldo_caja)
            } for caja in cajas]
            
            return JsonResponse({
                'success': True,
                'cajas': cajas_data
            })
            
        except Campamento.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'Campamento no encontrado'
            })
        except Exception as e:
            print(f"Error in handle_get_cajas: {e}")
            import traceback
            traceback.print_exc()
            return JsonResponse({
                'success': False,
                'error': f'Error interno: {str(e)}'
            })
    
    @staticmethod
    def handle_get_movimiento_desglose(request):
        """Handle movement breakdown request"""
        movimiento_id = request.GET.get('movimiento_id')
        
        if not movimiento_id:
            return JsonResponse({
                'success': False,
                'error': 'Movimiento ID es requerido'
            })
        
        try:
            # Try to find the movement in both ingreso and gasto models
            from apps.caja.models import MovimientoCajaIngreso, MovimientoCajaGasto
            
            movimiento = None
            try:
                movimiento = MovimientoCajaIngreso.objects.get(id=movimiento_id)
                content_type = ContentType.objects.get_for_model(MovimientoCajaIngreso)
            except MovimientoCajaIngreso.DoesNotExist:
                try:
                    movimiento = MovimientoCajaGasto.objects.get(id=movimiento_id)
                    content_type = ContentType.objects.get_for_model(MovimientoCajaGasto)
                except MovimientoCajaGasto.DoesNotExist:
                    pass
            
            if not movimiento:
                return JsonResponse({
                    'success': False,
                    'error': 'Movimiento no encontrado'
                })
            
            # Get movement breakdown
            movimientos_efectivo = MovimientoEfectivo.objects.filter(
                content_type=content_type,
                object_id=movimiento.id
            ).select_related('denominacion')
            
            desglose = {}
            for mov_efectivo in movimientos_efectivo:
                desglose[str(mov_efectivo.denominacion.id)] = {
                    'cantidad_entrada': mov_efectivo.cantidad_entrada,
                    'cantidad_salida': mov_efectivo.cantidad_salida
                }
            
            return JsonResponse({
                'success': True,
                'desglose': desglose
            })
            
        except Exception as e:
            print(f"Error in handle_get_movimiento_desglose: {e}")
            import traceback
            traceback.print_exc()
            return JsonResponse({
                'success': False,
                'error': f'Error interno: {str(e)}'
            })
    
    @staticmethod
    def handle_get_cuentas_vias(request):
        """Handle cuentas and vias request"""
        try:
            cuentas = CuentaBancaria.objects.filter(activo=True).order_by('nombre')
            vias = ViaMovimientoBanco.objects.all().order_by('nombre')
            
            cuentas_data = [{
                'id': cuenta.id,
                'nombre': cuenta.nombre,
                'IBAN': cuenta.IBAN
            } for cuenta in cuentas]
            
            vias_data = [{
                'id': via.id,
                'nombre': via.nombre
            } for via in vias]
            
            return JsonResponse({
                'success': True,
                'cuentas': cuentas_data,
                'vias': vias_data
            })
            
        except Exception as e:
            print(f"Error in handle_get_cuentas_vias: {e}")
            return JsonResponse({
                'success': False,
                'error': f'Error interno: {str(e)}'
            })


class LegacyAjaxHandler:
    """Handler for legacy caja-specific requests"""
    
    @staticmethod
    def handle_legacy_caja_request(request):
        """Handle legacy caja requests for backward compatibility"""
        caja_id = request.GET.get('caja_id')
        ejercicio_id = request.GET.get('ejercicio_id')
        
        if not caja_id:
            return JsonResponse({
                'success': False,
                'error': 'Caja ID es requerido para solicitudes legacy'
            })
        
        try:
            caja = Caja.objects.get(id=caja_id)
            
            # Get current breakdown for the caja
            desglose_actual = {}
            desgloses = DesgloseCaja.objects.filter(caja=caja).select_related('denominacion')
            
            for desglose in desgloses:
                desglose_actual[str(desglose.denominacion.id)] = {
                    'cantidad': desglose.cantidad,
                    'valor': float(desglose.denominacion.valor),
                    'es_billete': desglose.denominacion.es_billete
                }
            
            return JsonResponse({
                'success': True,
                'desglose_actual': desglose_actual
            })
            
        except Caja.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'Caja no encontrada'
            })
        except Exception as e:
            print(f"Error in handle_legacy_caja_request: {e}")
            import traceback
            traceback.print_exc()
            return JsonResponse({
                'success': False,
                'error': f'Error interno: {str(e)}'
            })
