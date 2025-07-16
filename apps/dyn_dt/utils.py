from django.db.models import Q
from django.utils import timezone
from datetime import datetime
from decimal import Decimal

def user_filter(request, queryset, fields, fk_fields=[]):
    """
    Filters a queryset based on search parameter in request.
    
    Args:
        request: Django request object
        queryset: QuerySet to filter
        fields: List of fields to search in
        fk_fields: List of foreign key fields to exclude from search
    
    Returns:
        Filtered queryset
    """
    value = request.GET.get('search')
    
    if value:
        dynamic_q = Q()
        for field in fields:
            if field not in fk_fields:
                dynamic_q |= Q(**{f'{field}__icontains': value})
        return queryset.filter(dynamic_q)

    return queryset


def combine_date_time(fecha_str, hora_str='12:00'):
    """
    Combines date and time strings into a timezone-aware datetime object.
    
    Args:
        fecha_str: Date string in 'YYYY-MM-DD' format
        hora_str: Time string in 'HH:MM' format
    
    Returns:
        Timezone-aware datetime object
    """
    fecha_datetime = datetime.strptime(f"{fecha_str} {hora_str}", '%Y-%m-%d %H:%M')
    return timezone.make_aware(fecha_datetime)


def get_model_field_names(model, field_type):
    """
    Returns a list of field names based on the given field type.
    
    Args:
        model: Django model class
        field_type: Django field type or tuple of field types
    
    Returns:
        List of field names
    """
    return [
        field.name for field in model._meta.get_fields() 
        if isinstance(field, field_type)
    ]


def format_movement_data(movement, tipo='caja'):
    """
    Formats movement data for JSON response.
    
    Args:
        movement: MovimientoCaja or MovimientoBanco instance
        tipo: Type of movement ('caja' or 'banco')
    
    Returns:
        Dictionary with formatted movement data
    """
    base_data = {
        'id': movement.id,
        'tipo': tipo,
        'fecha': movement.fecha.strftime('%Y-%m-%d'),
        'fecha_completa': movement.fecha.strftime('%Y-%m-%d %H:%M:%S'),
        'fecha_display': movement.fecha.strftime('%d/%m/%Y %H:%M'),
        'datetime_iso': movement.fecha.isoformat(),
        'concepto': str(movement.concepto),
        'concepto_id': movement.concepto.id,
        'cantidad': float(movement.cantidad),
        'es_gasto': movement.es_gasto(),
        'tiene_archivo': bool(movement.archivo_justificante),
        'archivo_url': movement.archivo_justificante.url if movement.archivo_justificante else None,
        'descripcion': movement.descripcion or ''
    }
    
    if tipo == 'caja':
        base_data.update({
            'caja': str(movement.caja),
            'caja_id': movement.caja.id,
            'turno': str(movement.turno),
            'turno_id': movement.turno.id,
            'justificante': movement.justificante or '',
        })
    else:  # banco
        base_data.update({
            'caja': f"Banco - {movement.ejercicio.nombre}",
            'caja_id': None,
            'turno': "Banco",
            'turno_id': None,
            'referencia_bancaria': getattr(movement, 'referencia_bancaria', '') or ''
        })
    
    return base_data


def calculate_movements_summary(movimientos):
    """
    Calculates summary statistics for a list of movements.
    
    Args:
        movimientos: List of movement objects
    
    Returns:
        Dictionary with summary statistics
    """
    total_ingresos = sum(mov.cantidad for mov in movimientos if not mov.es_gasto())
    total_gastos = sum(mov.cantidad for mov in movimientos if mov.es_gasto())
    
    return {
        'total_ingresos': float(total_ingresos),
        'total_gastos': float(total_gastos),
    }