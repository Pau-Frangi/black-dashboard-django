"""
AJAX request handlers for the dynamic datatables application.
"""
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from apps.dyn_dt.models import *
from apps.caja.models import *
from apps.banco.models import *
from apps.dyn_dt.utils import format_movement_data, calculate_movements_summary
from apps.caja.ajax_views import *
from apps.banco.ajax_views import *

class RegistroAjaxHandler:
    """Handles AJAX requests for the registro view."""
    
    @staticmethod
    def handle_get_ejercicio_movimientos(request):
        """
        Returns all movements for a specific ejercicio (both cash and bank).
        
        Args:
            request: Django request object with ejercicio_id parameter
            
        Returns:
            JsonResponse with movements data and summary
        """
        
        ejercicio_id = request.GET.get('ejercicio_id')
        campamento_id = request.GET.get('campamento_id')

        if not ejercicio_id or not campamento_id:
            return JsonResponse({'success': False, 'error': 'No se especificó un ejercicio o un campamento'})

        try:
            
            ejercicio = Ejercicio.objects.get(id=ejercicio_id)
            
            movimientos_caja_ingresos = get_movimientos_caja_ingresos(request)
            movimientos_caja_gastos = get_movimientos_caja_gastos(request)
            movimientos_caja_depositos = get_movimientos_caja_depositos(request)
            movimientos_caja_retiradas = get_movimientos_caja_retiradas(request)
            movimientos_caja_transferencias = get_movimientos_caja_transferencias(request)
            
            movimientos_banco_ingresos = get_movimientos_banco_ingreso(request)
            movimientos_banco_gastos = get_movimientos_banco_gasto(request)
            
            movimientos_data = []
            for mov in movimientos_caja_ingresos:
                movimientos_data.append(mov)
            for mov in movimientos_caja_gastos:
                movimientos_data.append(mov)
            for mov in movimientos_caja_depositos:
                movimientos_data.append(mov)
            for mov in movimientos_caja_retiradas:
                movimientos_data.append(mov)
            for mov in movimientos_caja_transferencias:
                movimientos_data.append(mov)
            for mov in movimientos_banco_ingresos:
                movimientos_data.append(mov)
            for mov in movimientos_banco_gastos:
                movimientos_data.append(mov)

            order_by = request.GET.get("order_by") or "-fecha"
            movimientos_data.sort(key=lambda x: x[order_by], reverse=True)

            resumen = calculate_movements_summary(movimientos_data)
            resumen['saldo_actual'] = float(ejercicio.saldo_total)

            return JsonResponse({
                'success': True,
                'movimientos': movimientos_data,
                'resumen': resumen,
                'ejercicio': {
                    'id': ejercicio.id,
                    'nombre': ejercicio.nombre,
                    'año': ejercicio.año,
                    'saldo_total': float(ejercicio.saldo_total)
                }
            })

        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    @staticmethod
    def handle_get_turnos(request):
        """
        Returns turnos for a specific ejercicio.
        
        Args:
            request: Django request object with ejercicio_id parameter
            
        Returns:
            JsonResponse with turnos list
        """
        ejercicio_id = request.GET.get('ejercicio_id')
        if not ejercicio_id:
            return JsonResponse({'success': False, 'error': 'No se especificó un ejercicio'})
        
        turnos = Turno.objects.filter(ejercicio_id=ejercicio_id).values('id', 'nombre')
        return JsonResponse({
            'success': True,
            'turnos': list(turnos)
        })
    
    @staticmethod
    def handle_get_cajas(request):
        """
        Returns list of cajas
        
        Args:
            request: Django request object with ejercicio_id parameter
            
        Returns:
            JsonResponse with cajas list
        """
        
        campamento_id = request.GET.get('campamento_id')
        campamento = get_object_or_404(Campamento, id=campamento_id) 

        cajas = Caja.objects.filter(campamento=campamento).values('id', 'nombre', 'saldo_caja', 'activa')

        return JsonResponse({
            'success': True,
            'cajas': list(cajas)
        })
    
    @staticmethod
    def handle_get_movimiento_desglose(request):
        """
        Returns money breakdown for a specific movement.
        
        Args:
            request: Django request object with movimiento_id parameter
            
        Returns:
            JsonResponse with desglose data
        """
        movimiento_id = request.GET.get('movimiento_id')
        if not movimiento_id:
            return JsonResponse({'success': False, 'error': 'No se especificó un movimiento'})
        
        try:
            movimiento = get_object_or_404(MovimientoCaja, id=movimiento_id)
            
            # Get the money breakdown for this movement
            desglose_data = {}
            for mov_dinero in movimiento.movimientos_dinero.all():
                desglose_data[mov_dinero.denominacion.id] = {
                    'cantidad_entrada': mov_dinero.cantidad_entrada,
                    'cantidad_salida': mov_dinero.cantidad_salida,
                    'cantidad_neta': mov_dinero.cantidad_neta(),
                    'valor': float(mov_dinero.denominacion.valor),
                    'valor_neto': float(mov_dinero.valor_neto())
                }
            
            return JsonResponse({
                'success': True,
                'desglose': desglose_data
            })
            
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
        
        
    @staticmethod
    def handle_get_cuentas_vias(request):
        """
        Devuelve una lista de cuentas bancarias y una lista de vías de movimiento bancario.
        Args:
            request: Django request object
        Returns:
            JsonResponse with cuentas and vias data
        """
        cuentas = CuentaBancaria.objects.filter(activo=True).values('id', 'nombre', 'titular', 'IBAN', 'activo')
        vias = ViaMovimientoBanco.objects.all().values('id', 'nombre')

        return JsonResponse({
            'success': True,
            'cuentas': list(cuentas),
            'vias': list(vias)
        })


class LegacyAjaxHandler:
    """Handles legacy AJAX requests for backward compatibility."""
    
    @staticmethod
    def handle_legacy_caja_request(request):
        """
        Handles legacy AJAX requests that are caja-specific.
        
        Args:
            request: Django request object with caja_id parameter
            
        Returns:
            JsonResponse with caja movements and breakdown
        """
        caja_id = request.GET.get('caja_id')
        ejercicio_id = request.GET.get('ejercicio_id')
        if not caja_id:
            return JsonResponse({'success': False, 'error': 'No se especificó una caja'})
        
        try:
            caja = get_object_or_404(Caja, id=caja_id)
            ejercicio = get_object_or_404(Ejercicio, id=ejercicio_id)
            
            # Get movements for this caja and its ejercicio
            movimientos_caja = MovimientoCaja.objects.filter(caja=caja, ejercicio=ejercicio).order_by('-id')
            movimientos_banco = MovimientoBanco.objects.filter(
                ejercicio=ejercicio
            ).order_by('-id')
            
            # Format movements data
            movimientos_data = []
            
            for mov in movimientos_caja:
                movimientos_data.append(format_movement_data(mov, 'caja'))
            
            for mov in movimientos_banco:
                movimientos_data.append(format_movement_data(mov, 'banco'))
            
            # Sort by date (most recent first)
            movimientos_data.sort(key=lambda x: x['datetime_iso'], reverse=True)
            
            # Calculate summary
            all_movimientos = list(movimientos_caja) + list(movimientos_banco)
            resumen = calculate_movements_summary(all_movimientos)
            resumen['saldo_actual'] = float(caja.saldo_caja)
            
            # Get current money breakdown
            desglose_actual = {}
            for desglose in caja.obtener_desglose_actual():
                desglose_actual[desglose.denominacion.id] = {
                    'cantidad': desglose.cantidad,
                    'valor': float(desglose.denominacion.valor),
                    'valor_total': float(desglose.valor_total())
                }
            
            return JsonResponse({
                'success': True,
                'movimientos': movimientos_data,
                'resumen': resumen,
                'desglose_actual': desglose_actual
            })
            
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
