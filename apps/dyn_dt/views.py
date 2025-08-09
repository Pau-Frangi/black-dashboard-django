"""
Main views module for dynamic datatables application.

This module coordinates between different handlers to provide
a clean, modular architecture for the application.
"""
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.conf import settings
from datetime import datetime

# Import modular handlers
from apps.dyn_dt.handlers.ajax_handlers import RegistroAjaxHandler, LegacyAjaxHandler
from apps.dyn_dt.handlers.movement_handlers import MovementHandler
from apps.dyn_dt.handlers.datatable_handlers import (
    DatatableHandler, FilterHandler, CRUDHandler, ExportHandler
)
from apps.dyn_dt.models import Concepto, Turno, Ejercicio, Campamento
from apps.caja.models import Caja, DenominacionEuro, MovimientoEfectivo, MovimientoCajaIngreso, MovimientoCajaGasto, MovimientoCajaDeposito, MovimientoCajaRetirada, MovimientoCajaTransferencia
from apps.banco.models import CuentaBancaria, ViaMovimientoBanco, MovimientoBancoGasto, MovimientoBancoIngreso

# ================================
# MAIN APPLICATION VIEWS
# ================================

def index(request):
    """
    Main index view for dynamic datatables.
    
    Args:
        request: Django request object
        
    Returns:
        Rendered index template with available routes
    """
    context = {
        'routes': settings.DYNAMIC_DATATB.keys(),
        'segment': 'dynamic_dt'
    }
    return render(request, 'dyn_dt/index.html', context)


@login_required
def registro(request):
    """
    Main view for movement registration (cash and bank).
    
    This view handles both AJAX requests for data retrieval
    and POST requests for movement operations.
    
    Args:
        request: Django request object
        
    Returns:
        JsonResponse for AJAX, rendered template for GET, 
        or JsonResponse for POST operations
    """
    # Handle AJAX requests for data retrieval
    if request.method == 'GET' and request.GET.get('ajax') == 'true':
        return _handle_ajax_requests(request)
    
    # Handle POST requests for movement operations
    if request.method == 'POST':
        return _handle_movement_operations(request)
    
    # GET request - render the registration template
    context = _get_registro_context()
    return render(request, 'pages/registro.html', context)


@login_required
def saldo(request):
    """
    Vista principal para operaciones de saldo por ejercicio.
    Permite seleccionar un ejercicio y muestra gráficos y estadísticas
    agregadas de movimientos de caja y banco, así como desgloses.
    """
    if request.method == 'GET' and request.GET.get('ajax') == 'true':
        from django.http import JsonResponse
        from django.db.models import Sum, Q, F

        ejercicio_id = request.GET.get('ejercicio_id')
        if not ejercicio_id:
            return JsonResponse({'success': False, 'error': 'Ejercicio ID requerido'})

        try:
            ejercicio = Ejercicio.objects.get(id=ejercicio_id)
        except Ejercicio.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Ejercicio no encontrado'})

        # Movimientos de caja y banco
        movimientos_caja = MovimientoCaja.objects.filter(ejercicio=ejercicio).select_related('caja', 'turno', 'concepto').order_by('-fecha')
        movimientos_banco = MovimientoBanco.objects.filter(ejercicio=ejercicio).select_related('turno', 'concepto').order_by('-fecha')

        # Unificar movimientos para gráficos de evolución
        all_movimientos = []
        for mov in movimientos_caja:
            all_movimientos.append({
                'id': mov.id,
                'tipo': 'caja',
                'fecha': mov.fecha.strftime('%Y-%m-%d'),
                'fecha_display': mov.fecha.strftime('%d/%m/%Y %H:%M'),
                'datetime_iso': mov.fecha.isoformat(),
                'turno': mov.turno.nombre,
                'turno_id': mov.turno.id,
                'concepto': mov.concepto.nombre,
                'concepto_id': mov.concepto.id,
                'descripcion': mov.descripcion,
                'cantidad': float(mov.cantidad),
                'es_gasto': mov.concepto.es_gasto,
                'justificante': mov.justificante,
                'caja': mov.caja.nombre,
                'caja_id': mov.caja.id,
                'referencia_bancaria': None
            })
        for mov in movimientos_banco:
            all_movimientos.append({
                'id': mov.id,
                'tipo': 'banco',
                'fecha': mov.fecha.strftime('%Y-%m-%d'),
                'fecha_display': mov.fecha.strftime('%d/%m/%Y %H:%M'),
                'datetime_iso': mov.fecha.isoformat(),
                'turno': mov.turno.nombre if mov.turno else 'N/A',
                'turno_id': mov.turno.id if mov.turno else None,
                'concepto': mov.concepto.nombre,
                'concepto_id': mov.concepto.id,
                'descripcion': mov.descripcion,
                'cantidad': float(mov.cantidad),
                'es_gasto': mov.concepto.es_gasto,
                'justificante': '',
                'caja': None,
                'caja_id': None,
                'referencia_bancaria': mov.referencia_bancaria
            })
        # Ordenar por fecha descendente
        all_movimientos.sort(key=lambda x: x['datetime_iso'], reverse=True)

        # Resumen de totales
        total_ingresos_caja = movimientos_caja.filter(concepto__es_gasto=False).aggregate(total=Sum('cantidad'))['total'] or 0
        total_gastos_caja = movimientos_caja.filter(concepto__es_gasto=True).aggregate(total=Sum('cantidad'))['total'] or 0
        total_ingresos_banco = movimientos_banco.filter(concepto__es_gasto=False).aggregate(total=Sum('cantidad'))['total'] or 0
        total_gastos_banco = movimientos_banco.filter(concepto__es_gasto=True).aggregate(total=Sum('cantidad'))['total'] or 0

        total_ingresos = float(total_ingresos_caja + total_ingresos_banco)
        total_gastos = float(total_gastos_caja + total_gastos_banco)
        saldo_actual = float(ejercicio.saldo_total)
        total_movimientos = len(all_movimientos)

        resumen = {
            'total_ingresos': total_ingresos,
            'total_gastos': total_gastos,
            'saldo_actual': saldo_actual,
            'total_movimientos': total_movimientos
        }

        # Evolución del saldo (por día)
        balance_evolution = []
        movimientos_sorted = sorted(all_movimientos, key=lambda x: x['datetime_iso'])
        running_balance = saldo_actual
        for mov in reversed(movimientos_sorted):
            balance_evolution.append({
                'fecha': mov['fecha'],
                'balance': running_balance,
                'movimiento': mov['cantidad'] if not mov['es_gasto'] else -mov['cantidad'],
                'tipo': mov['tipo'],
                'concepto': mov['concepto'],
            })
            running_balance -= mov['cantidad'] if not mov['es_gasto'] else -mov['cantidad']

        balance_evolution = list(reversed(balance_evolution))

        # Desglose por conceptos (ingresos/gastos por concepto)
        concept_data = {}
        conceptos = Concepto.objects.all()
        for concepto in conceptos:
            total_caja = movimientos_caja.filter(concepto=concepto).aggregate(total=Sum('cantidad'))['total'] or 0
            total_banco = movimientos_banco.filter(concepto=concepto).aggregate(total=Sum('cantidad'))['total'] or 0
            total = float(total_caja + total_banco)
            if total > 0:
                concept_data[concepto.nombre] = {
                    'total': total,
                    'tipo': 'gasto' if concepto.es_gasto else 'ingreso'
                }

        # Desglose actual de todas las cajas del ejercicio
        desglose_actual = []
        cajas = Caja.objects.all()
        for caja in cajas:
            for desglose in caja.obtener_desglose_actual():
                desglose_actual.append({
                    'caja': caja.nombre,
                    'valor': float(desglose.denominacion.valor),
                    'es_billete': desglose.denominacion.es_billete,
                    'cantidad': desglose.cantidad,
                    'valor_total': float(desglose.valor_total())
                })

        # Movimientos recientes (últimos 10)
        recent_movements = all_movimientos[:10]

        # Info de cajas y banco
        caja_info = {
            'cajas': [{
                'id': caja.id,
                'nombre': caja.nombre,
                'saldo_actual': float(caja.saldo_caja)
            } for caja in cajas],
            'saldo_banco': float(ejercicio.saldo_banco),
            'saldo_actual': saldo_actual
        }

        return JsonResponse({
            'success': True,
            'ejercicio': {
                'id': ejercicio.id,
                'nombre': ejercicio.nombre,
                'año': ejercicio.año
            },
            'movimientos': all_movimientos,
            'resumen': resumen,
            'balance_evolution': balance_evolution,
            'concept_data': concept_data,
            'desglose_actual': desglose_actual,
            'recent_movements': recent_movements,
            'caja_info': caja_info,
        })

    # --- FIN AJAX ---
    context = {
        'ejercicios': Ejercicio.objects.all().order_by('-año', 'nombre'),
        'default_ejercicio_id': None,  # Añadido para compatibilidad con registro
        'segment': 'saldo'
    }
    ejercicios = context['ejercicios']
    current_year = datetime.now().year
    default_ejercicio = None
    for ejercicio in ejercicios:
        if ejercicio.año == current_year:
            default_ejercicio = ejercicio
            break
    if not default_ejercicio and ejercicios.exists():
        default_ejercicio = ejercicios.first()
    context['default_ejercicio_id'] = default_ejercicio.id if default_ejercicio else None
    return render(request, 'pages/saldo.html', context)


@login_required
def tables(request):
    """
    Main view for tables display and management.
    
    Args:
        request: Django request object
        
    Returns:
        Rendered tables template or JsonResponse for AJAX
    """
    # Handle AJAX requests for tables data
    if request.method == 'GET' and request.GET.get('ajax') == 'true':
        return _handle_tables_ajax_requests(request)
    
    # GET request - render the tables template
    context = _get_tables_context()
    return render(request, 'pages/tables.html', context)


@login_required
def cajas(request):
    """
    Vista principal para gestión de cajas.
    También responde a AJAX para datos de cajas, desglose, movimientos, etc.
    """
    from django.http import JsonResponse
    from django.db.models import Sum
    # AJAX handler
    if request.method == 'GET' and request.GET.get('ajax') == 'true':
        action = request.GET.get('action')

        if not action:
            cajas = Caja.objects.all()
            cajas_data = [{
                'id': caja.id,
                'nombre': caja.nombre,
                'activa': caja.activa,
                'saldo_caja': float(caja.saldo_caja),
                'ingresos_caja': float(caja.movimientos.filter(concepto__es_gasto=False).aggregate(Sum('cantidad'))['cantidad__sum'] or 0),
                'gastos_caja': float(caja.movimientos.filter(concepto__es_gasto=True).aggregate(Sum('cantidad'))['cantidad__sum'] or 0)
            } for caja in cajas]
            return JsonResponse({'success': True, 'cajas': cajas_data})
        # Desglose de caja
        elif action == 'get_desglose':
            caja_id = request.GET.get('caja_id')
            if not caja_id:
                return JsonResponse({'success': False, 'error': 'Caja ID requerido'})
            try:
                caja = Caja.objects.get(id=caja_id)
            except Caja.DoesNotExist:
                return JsonResponse({'success': False, 'error': 'Caja no encontrada'})
            desglose = caja.obtener_desglose_actual()
            desglose_data = [{
                'denominacion': str(d.denominacion),
                'cantidad': d.cantidad,
                'valor_total': float(d.valor_total()),
                'tipo': 'billete' if getattr(d.denominacion, 'es_billete', False) else 'moneda'
            } for d in desglose]
            return JsonResponse({'success': True, 'desglose': desglose_data})
        # Movimientos de caja
        elif action == 'get_movimientos':
            caja_id = request.GET.get('caja_id')
            if not caja_id:
                return JsonResponse({'success': False, 'error': 'Caja ID requerido'})
            try:
                caja = Caja.objects.get(id=caja_id)
            except Caja.DoesNotExist:
                return JsonResponse({'success': False, 'error': 'Caja no encontrada'})
            movimientos = caja.movimientos.select_related('turno', 'concepto').order_by('-fecha')
            movimientos_data = [{
                'id': mov.id,
                'fecha_display': mov.fecha.strftime('%d/%m/%Y %H:%M'),
                'concepto': mov.concepto.nombre,
                'cantidad': float(mov.cantidad),
                'es_gasto': mov.concepto.es_gasto
            } for mov in movimientos]
            return JsonResponse({'success': True, 'movimientos': movimientos_data})
        # Movimientos de dinero
        elif action == 'get_movimientos_dinero':
            caja_id = request.GET.get('caja_id')
            if not caja_id:
                return JsonResponse({'success': False, 'error': 'Caja ID requerido'})
            try:
                caja = Caja.objects.get(id=caja_id)
            except Caja.DoesNotExist:
                return JsonResponse({'success': False, 'error': 'Caja no encontrada'})
            movimientos_dinero = []
            for mov in caja.movimientos.all():
                for md in mov.movimientos_dinero.all():
                    movimientos_dinero.append({
                        'denominacion': str(md.denominacion),
                        'cantidad_entrada': md.cantidad_entrada,
                        'cantidad_salida': md.cantidad_salida
                    })
            return JsonResponse({'success': True, 'movimientos_dinero': movimientos_dinero})
        # Gráficos de utilidad (ejemplo: saldo por día)
        elif action == 'get_graficos':
            caja_id = request.GET.get('caja_id')
            if not caja_id:
                return JsonResponse({'success': False, 'error': 'Caja ID requerido'})
            try:
                caja = Caja.objects.get(id=caja_id)
            except Caja.DoesNotExist:
                return JsonResponse({'success': False, 'error': 'Caja no encontrada'})
            movimientos = caja.movimientos.order_by('fecha')
            labels = []
            saldos = []
            saldo = 0
            for mov in movimientos:
                saldo += mov.cantidad_real()
                labels.append(mov.fecha.strftime('%d/%m'))
                saldos.append(float(saldo))
            return JsonResponse({'success': True, 'grafico': {'labels': labels, 'saldos': saldos}})
        else:
            return JsonResponse({'success': False, 'error': 'Acción no válida'})
    # Render HTML
    ejercicios = Ejercicio.objects.all().order_by('-año', 'nombre')
    current_year = datetime.now().year
    default_ejercicio = None
    for ejercicio in ejercicios:
        if ejercicio.año == current_year:
            default_ejercicio = ejercicio
            break
    if not default_ejercicio and ejercicios.exists():
        default_ejercicio = ejercicios.first()
    context = {
        'ejercicios': ejercicios,
        'default_ejercicio_id': default_ejercicio.id if default_ejercicio else None,
        'segment': 'cajas'
    }
    return render(request, 'pages/cajas.html', context)


def _handle_ajax_requests(request):
    """
    Routes AJAX requests to appropriate handlers.
    
    Args:
        request: Django request object with AJAX parameters
        
    Returns:
        JsonResponse from appropriate handler
    """
    # New ejercicio-based requests
    if request.GET.get('get_ejercicio_movimientos') == 'true':
        return RegistroAjaxHandler.handle_get_ejercicio_movimientos(request)
    elif request.GET.get('get_turnos') == 'true':
        return RegistroAjaxHandler.handle_get_turnos(request)
    elif request.GET.get('get_cajas') == 'true':
        return RegistroAjaxHandler.handle_get_cajas(request)
    elif request.GET.get('get_movimiento_desglose') == 'true':
        return RegistroAjaxHandler.handle_get_movimiento_desglose(request)
    elif request.GET.get('get_cuentas_vias') == 'true':
        return RegistroAjaxHandler.handle_get_cuentas_vias(request)
    else:
        # Legacy caja-specific requests for backward compatibility
        return LegacyAjaxHandler.handle_legacy_caja_request(request)


def _handle_movement_operations(request):
    """
    Routes POST requests for movement operations.
    
    Args:
        request: Django request object with action parameter
        
    Returns:
        JsonResponse from appropriate handler
    """
    action = request.POST.get('action')
    
    if action == 'add':
        return MovementHandler.create_movement(request)  # request contains user
    elif action == 'delete':
        return MovementHandler.delete_movement(request)
    elif action == 'edit':
        return MovementHandler.edit_movement(request)
    else:
        from django.http import JsonResponse
        return JsonResponse({'success': False, 'error': 'Acción no válida'})


def _get_registro_context():
    """
    Prepares context data for the registro template.
    
    Returns:
        Dictionary with context data for the template
    """
    
    campamentos = Campamento.objects.all().order_by('nombre')
    default_campamento = campamentos.first() if campamentos.exists() else None
    
    ejercicios = Ejercicio.objects.all().order_by('-año', 'nombre')
    
    # Determine default ejercicio - current year first, then highest year
    current_year = datetime.now().year
    default_ejercicio = None
    
    # Try to find ejercicio for current year
    for ejercicio in ejercicios:
        if ejercicio.año == current_year:
            default_ejercicio = ejercicio
            break
    
    # If no ejercicio for current year, get the one with highest year
    if not default_ejercicio and ejercicios.exists():
        default_ejercicio = ejercicios.first()  # Already ordered by -año
    
    return {
        'campamentos': campamentos,
        'default_campamento_id': default_campamento.id if default_campamento else None,
        'ejercicios': ejercicios,
        'cajas': Caja.objects.all().order_by('nombre'),
        'conceptos': Concepto.objects.all(),
        'denominaciones': DenominacionEuro.objects.filter(activa=True).order_by('-valor'),
        'default_ejercicio_id': default_ejercicio.id if default_ejercicio else None,
        'segment': 'registro'
    }


def _handle_tables_ajax_requests(request):
    """
    Routes AJAX requests for tables to appropriate handlers.
    
    Args:
        request: Django request object with AJAX parameters
        
    Returns:
        JsonResponse from appropriate handler
    """
    
    campamento_id = request.GET.get('campamento_id')
    ejercicio_id = request.GET.get('ejercicio_id')
    
    if ejercicio_id and campamento_id:
        # Handle ejercicio-based tables request
        return _handle_campamento_ejercicio_tables_request(request, ejercicio_id, campamento_id)
    else:
        from django.http import JsonResponse
        return JsonResponse({'success': False, 'error': 'Ejercicio ID y Campamento ID requeridos'})


def _handle_campamento_ejercicio_tables_request(request, ejercicio_id, campamento_id):
    """
    Handle tables data request for a specific ejercicio.
    
    Args:
        request: Django request object
        ejercicio_id: ID of the ejercicio
        
    Returns:
        JsonResponse with tables data
    """
    from django.http import JsonResponse
    from django.db.models import Sum, Count, Q
    from apps.dyn_dt.models import MovimientoCaja, MovimientoBanco
    
    try:
        
        campamento = Campamento.objects.get(id=campamento_id)
        ejercicio = Ejercicio.objects.get(id=ejercicio_id)
        
        # Get all movements for this ejercicio (both caja and banco)
        movimientos_caja = MovimientoCaja.objects.filter(ejercicio=ejercicio, caja__campamento=campamento)
        movimientos_banco = MovimientoBanco.objects.filter(ejercicio=ejercicio, campamento=campamento)

        # Calculate conceptos data
        conceptos_data = []
        
        # Process concepto data from caja movements
        conceptos_caja = movimientos_caja.values('concepto__id', 'concepto__nombre', 'concepto__es_gasto').annotate(
            total=Sum('cantidad'),
            count=Count('id')
        )
        
        # Process concepto data from banco movements
        conceptos_banco = movimientos_banco.values('concepto__id', 'concepto__nombre', 'concepto__es_gasto').annotate(
            total=Sum('cantidad'),
            count=Count('id')
        )
        
        # Combine concepto data
        conceptos_dict = {}
        
        for concepto in conceptos_caja:
            concepto_id = concepto['concepto__id']
            if concepto_id not in conceptos_dict:
                conceptos_dict[concepto_id] = {
                    'id': concepto_id,
                    'nombre': concepto['concepto__nombre'],
                    'es_gasto': concepto['concepto__es_gasto'],
                    'total': 0,
                    'count': 0
                }
            conceptos_dict[concepto_id]['total'] += float(concepto['total'] or 0)
            conceptos_dict[concepto_id]['count'] += concepto['count']
        
        for concepto in conceptos_banco:
            concepto_id = concepto['concepto__id']
            if concepto_id not in conceptos_dict:
                conceptos_dict[concepto_id] = {
                    'id': concepto_id,
                    'nombre': concepto['concepto__nombre'],
                    'es_gasto': concepto['concepto__es_gasto'],
                    'total': 0,
                    'count': 0
                }
            conceptos_dict[concepto_id]['total'] += float(concepto['total'] or 0)
            conceptos_dict[concepto_id]['count'] += concepto['count']
        
        conceptos_data = list(conceptos_dict.values())
        
        # Calculate turnos data (combine both caja and banco movements)
        turnos_data = []
        
        # Get all turnos for the currento ejercicio of the campamento
        turnos_ejercicio_campamento = ejercicio.turnos.filter(campamento=campamento)

        for turno in turnos_ejercicio_campamento:
            # Calculate totals for this turno from caja movements
            caja_ingresos = movimientos_caja.filter(
                turno=turno, concepto__es_gasto=False
            ).aggregate(total=Sum('cantidad'))['total'] or 0
            
            caja_gastos = movimientos_caja.filter(
                turno=turno, concepto__es_gasto=True
            ).aggregate(total=Sum('cantidad'))['total'] or 0
            
            caja_count = movimientos_caja.filter(turno=turno).count()
            
            # Calculate totals for this turno from banco movements
            banco_ingresos = movimientos_banco.filter(
                turno=turno, concepto__es_gasto=False
            ).aggregate(total=Sum('cantidad'))['total'] or 0
            
            banco_gastos = movimientos_banco.filter(
                turno=turno, concepto__es_gasto=True
            ).aggregate(total=Sum('cantidad'))['total'] or 0
            
            banco_count = movimientos_banco.filter(turno=turno).count()
            
            # Combine totals
            total_ingresos = float(caja_ingresos + banco_ingresos)
            total_gastos = float(caja_gastos + banco_gastos)
            total_count = caja_count + banco_count
            
            # Only include turnos that have movements
            if total_count > 0:
                turnos_data.append({
                    'id': turno.id,
                    'nombre': turno.nombre,
                    'ingresos': total_ingresos,
                    'gastos': total_gastos,
                    'count': total_count
                })
        
        # Calculate resumen
        total_ingresos_caja = movimientos_caja.filter(concepto__es_gasto=False).aggregate(Sum('cantidad'))['cantidad__sum'] or 0
        total_gastos_caja = movimientos_caja.filter(concepto__es_gasto=True).aggregate(Sum('cantidad'))['cantidad__sum'] or 0
        
        total_ingresos_banco = movimientos_banco.filter(concepto__es_gasto=False).aggregate(Sum('cantidad'))['cantidad__sum'] or 0
        total_gastos_banco = movimientos_banco.filter(concepto__es_gasto=True).aggregate(Sum('cantidad'))['cantidad__sum'] or 0
        
        total_ingresos = float(total_ingresos_caja + total_ingresos_banco)
        total_gastos = float(total_gastos_caja + total_gastos_banco)
        saldo_actual = float(ejercicio.calcular_resultado_ejercicio(campamento=campamento))

        resumen = {
            'total_ingresos': total_ingresos,
            'total_gastos': total_gastos,
            'saldo_actual': saldo_actual
        }
        
        return JsonResponse({
            'success': True,
            'ejercicio': {
                'id': ejercicio.id,
                'nombre': ejercicio.nombre,
                'año': ejercicio.año
            },
            'conceptos': conceptos_data,
            'turnos': turnos_data,
            'resumen': resumen
        })
        
    except Ejercicio.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Ejercicio no encontrado'})
    except Exception as e:
        import traceback
        print(f"Error in _handle_campamento_ejercicio_tables_request: {e}")
        print(traceback.format_exc())
        return JsonResponse({'success': False, 'error': str(e)})


def _get_tables_context():
    """
    Prepares context data for the tables template.
    
    Returns:
        Dictionary with context data for the template
    """
    ejercicios = Ejercicio.objects.all().order_by('-año', 'nombre')
    
    # Determine default ejercicio - current year first, then highest year
    current_year = datetime.now().year
    default_ejercicio = None
    
    # Try to find ejercicio for current year
    for ejercicio in ejercicios:
        if ejercicio.año == current_year:
            default_ejercicio = ejercicio
            break
    
    # If no ejercicio for current year, get the one with highest year
    if not default_ejercicio and ejercicios.exists():
        default_ejercicio = ejercicios.first()  # Already ordered by -año
    
    return {
        'campamentos': Campamento.objects.all().order_by('nombre'),
        'ejercicios': ejercicios,
        'default_ejercicio_id': default_ejercicio.id if default_ejercicio else None,
        'routes': settings.DYNAMIC_DATATB.keys(),
        'segment': 'tables'
    }


# ================================
# DYNAMIC DATATABLE VIEWS
# ================================

def model_dt(request, aPath):
    """
    Main view for dynamic datatables display and management.
    
    Args:
        request: Django request object
        aPath: Model path string
        
    Returns:
        Rendered datatable template or redirect on pagination error
    """
    # Get model class and validate
    aModelName, aModelClass = DatatableHandler.get_model_data(aPath)
    if not aModelClass:
        return HttpResponse(f' > ERR: Getting ModelClass for path: {aPath}')
    
    # Prepare model context data
    model_context = DatatableHandler.prepare_model_context(aModelClass, aPath)
    
    # Apply filters and pagination
    pagination_result = DatatableHandler.apply_filters_and_pagination(
        request, aModelClass, aPath, 
        model_context['db_fields'], 
        model_context['fk_fields']
    )
    
    # Handle pagination errors
    if pagination_result is None:
        return redirect('model_dt', aPath=aPath)
    
    items, p_items, filter_instance = pagination_result
    
    # Build complete context
    context = {
        'page_title': f'Dynamic DataTable - {aPath.lower().title()}',
        'link': aPath,
        'items': items,
        'page_items': p_items,
        'filter_instance': filter_instance,
        'read_only_fields': ('id',),
        'segment': 'dynamic_dt',
        # Add model context data
        **model_context,
        # Flatten field types for template
        **model_context['field_types'],
        # Additional template data
        'fk_fields_keys': list(model_context['fk_fields'].keys()),
    }
    
    return render(request, 'dyn_dt/model.html', context)


# ================================
# FILTER MANAGEMENT VIEWS
# ================================

def create_filter(request, model_name):
    """Creates or updates model filters."""
    return FilterHandler.create_filter(request, model_name)


def delete_filter(request, model_name, id):
    """Deletes a specific filter."""
    return FilterHandler.delete_filter(request, model_name, id)


def create_hide_show_filter(request, model_name):
    """Creates or updates field visibility filters."""
    return FilterHandler.create_hide_show_filter(request, model_name)


def create_page_items(request, model_name):
    """Updates pagination settings."""
    return FilterHandler.create_page_items(request, model_name)


# ================================
# CRUD OPERATION VIEWS
# ================================

@login_required(login_url='/accounts/login/')

def create(request, aPath):    
    """Creates a new model instance."""
    return CRUDHandler.create_item(request, aPath)


@login_required(login_url='/accounts/login/')
def update(request, aPath, id):
    """Updates an existing model instance."""
    return CRUDHandler.update_item(request, aPath, id)


@login_required(login_url='/accounts/login/')
def delete(request, aPath, id):
    """Deletes a model instance."""
    return CRUDHandler.delete_item(request, aPath, id)


# ================================
# EXPORT VIEWS
# ================================
def export_csv(request, aPath):
    """Handles CSV export requests."""
    return ExportHandler.export_csv(request, aPath)