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
from apps.dyn_dt.models import Ejercicio, Caja, Concepto, DenominacionEuro


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
    Main view for balance/saldo operations.
    
    Args:
        request: Django request object
        
    Returns:
        Rendered saldo template
    """
    context = {
        'ejercicios': Ejercicio.objects.all().order_by('-año', 'nombre'),
        'cajas': Caja.objects.all().order_by('-año', 'nombre'),
        'segment': 'saldo'
    }
    return render(request, 'pages/saldo.html', context)


@login_required
def tables(request):
    """
    Main view for tables display and management.
    
    Args:
        request: Django request object
        
    Returns:
        Rendered tables template
    """
    context = {
        'routes': settings.DYNAMIC_DATATB.keys(),
        'segment': 'tables'
    }
    return render(request, 'pages/tables.html', context)


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
        return MovementHandler.create_movement(request)
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
        'ejercicios': ejercicios,
        'cajas': Caja.objects.all().order_by('-año', 'nombre'),
        'conceptos': Concepto.objects.all(),
        'denominaciones': DenominacionEuro.objects.filter(activa=True).order_by('-valor'),
        'default_ejercicio_id': default_ejercicio.id if default_ejercicio else None,
        'segment': 'registro'
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