import requests, base64, json, csv
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.http import HttpResponse, JsonResponse
from django.utils.safestring import mark_safe
from django.conf import settings
from django.urls import reverse
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.urls import reverse
from decimal import Decimal
from django.views import View
from django.db import models
from pprint import pp 

from apps.dyn_dt.models import ModelFilter, PageItems, HideShowFilter, Caja, MovimientoCaja, Turno, Concepto, DenominacionEuro, MovimientoDinero
from apps.dyn_dt.utils import user_filter
from apps.dyn_dt.forms import MovimientoCajaForm, DesgloseDineroForm

from cli import *

# Create your views here.

def index(request):
    
    context = {
        'routes' : settings.DYNAMIC_DATATB.keys(),
        'segment': 'dynamic_dt'
    }

    return render(request, 'dyn_dt/index.html', context)

def create_filter(request, model_name):
    model_name = model_name.lower()
    if request.method == "POST":
        keys = request.POST.getlist('key')
        values = request.POST.getlist('value')
        for i in range(len(keys)):
            key = keys[i]
            value = values[i]

            ModelFilter.objects.update_or_create(
                parent=model_name,
                key=key,
                defaults={'value': value}
            )

        return redirect(reverse('model_dt', args=[model_name]))


def create_page_items(request, model_name):
    model_name = model_name.lower()
    if request.method == 'POST':
        items = request.POST.get('items')
        page_items, created = PageItems.objects.update_or_create(
            parent=model_name,
            defaults={'items_per_page':items}
        )
        return redirect(reverse('model_dt', args=[model_name]))


def create_hide_show_filter(request, model_name):
    model_name = model_name.lower()
    if request.method == "POST":
        data_str = list(request.POST.keys())[0]
        data = json.loads(data_str)

        HideShowFilter.objects.update_or_create(
            parent=model_name,
            key=data.get('key'),
            defaults={'value': data.get('value')}
        )

        response_data = {'message': 'Model updated successfully'}
        return JsonResponse(response_data)

    return JsonResponse({'error': 'Invalid request'}, status=400)


def delete_filter(request, model_name, id):
    model_name = model_name.lower()
    filter_instance = ModelFilter.objects.get(id=id, parent=model_name)
    filter_instance.delete()
    return redirect(reverse('model_dt', args=[model_name]))


def get_model_field_names(model, field_type):
    """Returns a list of field names based on the given field type."""
    return [
        field.name for field in model._meta.get_fields() 
        if isinstance(field, field_type)
    ]

def model_dt(request, aPath):
    aModelName  = None
    aModelClass = None
    choices_dict = {}

    if aPath in settings.DYNAMIC_DATATB.keys():
        aModelName  = settings.DYNAMIC_DATATB[aPath]
        aModelClass = name_to_class(aModelName)

    if not aModelClass:
        return HttpResponse( ' > ERR: Getting ModelClass for path: ' + aPath )
    
    #db_fields = [field.name for field in aModelClass._meta.get_fields() if not field.is_relation]
    db_fields = [field.name for field in aModelClass._meta.fields]
    fk_fields = get_model_fk_values(aModelClass)
    db_filters = []
    for f in db_fields:
        if f not in fk_fields.keys():
            db_filters.append( f )

    for field in aModelClass._meta.fields:
        if field.choices:
            choices_dict[field.name] = field.choices

    field_names = []
    for field_name in db_fields:
        fields, created = HideShowFilter.objects.get_or_create(key=field_name, parent=aPath.lower())
        if fields.key in db_fields:
            field_names.append(fields)
    
    model_series = {}
    for f in db_fields:
        f_values = list ( aModelClass.objects.values_list( f, flat=True) )
        model_series[ f ] = ', '.join( str(i) for i in f_values)

    # model filter
    filter_string = {}
    filter_instance = ModelFilter.objects.filter(parent=aPath.lower())
    for filter_data in filter_instance:
        if filter_data.key in db_fields: 
            filter_string[f'{filter_data.key}__icontains'] = filter_data.value

    order_by = request.GET.get('order_by', 'id')
    if order_by not in db_fields:
        order_by = 'id'
    
    queryset = aModelClass.objects.filter(**filter_string).order_by(order_by)
    item_list = user_filter(request, queryset, db_fields, fk_fields.keys())

    # pagination
    page_items = PageItems.objects.filter(parent=aPath.lower()).last()
    p_items = 25
    if page_items:
        p_items = page_items.items_per_page

    page = request.GET.get('page', 1)
    paginator = Paginator(item_list, p_items)

    try:
        items = paginator.page(page)
    except PageNotAnInteger:
        return redirect(reverse('model_dt', args=[aPath]))
    except EmptyPage:
        return redirect(reverse('model_dt', args=[aPath]))
    
    read_only_fields = ('id', )

    integer_fields = get_model_field_names(aModelClass, models.IntegerField)
    date_time_fields = get_model_field_names(aModelClass, models.DateTimeField)
    email_fields = get_model_field_names(aModelClass, models.EmailField)
    text_fields = get_model_field_names(aModelClass, (models.TextField, models.CharField))
    
    context = {
        'page_title': 'Dynamic DataTable - ' + aPath.lower().title(),
        'link': aPath,
        'field_names': field_names,
        'db_field_names': db_fields,
        'db_filters': db_filters,
        'items': items,
        'page_items': p_items,
        'filter_instance': filter_instance,
        'read_only_fields': read_only_fields,

        'integer_fields': integer_fields,
        'date_time_fields': date_time_fields,
        'email_fields': email_fields,
        'text_fields': text_fields,
        'fk_fields_keys': list( fk_fields.keys() ),
        'fk_fields': fk_fields ,
        'choices_dict': choices_dict,
        'segment': 'dynamic_dt'
    }
    return render(request, 'dyn_dt/model.html', context)


@login_required(login_url='/accounts/login/')
def create(request, aPath):
    aModelClass = None

    if aPath in settings.DYNAMIC_DATATB.keys():
        aModelName  = settings.DYNAMIC_DATATB[aPath]
        aModelClass = name_to_class(aModelName)

    if not aModelClass:
        return HttpResponse( ' > ERR: Getting ModelClass for path: ' + aPath )

    if request.method == 'POST':
        data = {}
        fk_fields = get_model_fk(aModelClass)

        for attribute, value in request.POST.items():
            if attribute == 'csrfmiddlewaretoken':
                continue

            # Process FKs    
            if attribute in fk_fields.keys():
                value = name_to_class( fk_fields[attribute] ).objects.filter(id=value).first()
            
            data[attribute] = value if value else ''

        aModelClass.objects.create(**data)

    return redirect(request.META.get('HTTP_REFERER'))


@login_required(login_url='/accounts/login/')
def delete(request, aPath, id):
    aModelClass = None

    if aPath in settings.DYNAMIC_DATATB.keys():
        aModelName  = settings.DYNAMIC_DATATB[aPath]
        aModelClass = name_to_class(aModelName)

    if not aModelClass:
        return HttpResponse( ' > ERR: Getting ModelClass for path: ' + aPath )
    
    item = aModelClass.objects.get(id=id)
    item.delete()
    return redirect(request.META.get('HTTP_REFERER'))


@login_required(login_url='/accounts/login/')
def update(request, aPath, id):
    aModelClass = None

    if aPath in settings.DYNAMIC_DATATB.keys():
        aModelName  = settings.DYNAMIC_DATATB[aPath]
        aModelClass = name_to_class(aModelName)

    if not aModelClass:
        return HttpResponse( ' > ERR: Getting ModelClass for path: ' + aPath )

    item = aModelClass.objects.get(id=id)
    fk_fields = get_model_fk(aModelClass)

    if request.method == 'POST':
        for attribute, value in request.POST.items():

            if attribute == 'csrfmiddlewaretoken':
                continue

            if getattr(item, attribute, value) is not None:

                # Process FKs    
                if attribute in fk_fields.keys():
                    value = name_to_class( fk_fields[attribute] ).objects.filter(id=value).first()

                setattr(item, attribute, value)
        
        item.save()

    return redirect(request.META.get('HTTP_REFERER'))



# Export as CSV
class ExportCSVView(View):
    def get(self, request, aPath):
        aModelName  = None
        aModelClass = None

        if aPath in settings.DYNAMIC_DATATB.keys():
            aModelName  = settings.DYNAMIC_DATATB[aPath]
            aModelClass = name_to_class(aModelName)

        if not aModelClass:
            return HttpResponse( ' > ERR: Getting ModelClass for path: ' + aPath )
        
        db_field_names = [field.name for field in aModelClass._meta.get_fields()]
        fields = []
        show_fields = HideShowFilter.objects.filter(value=False, parent=aPath.lower())
        
        for field in show_fields:
            if field.key in db_field_names:
                fields.append(field.key)
            else:
                print(f"Field {field.key} does not exist in {aModelClass} model.")

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="{aPath.lower()}.csv"'

        writer = csv.writer(response)
        writer.writerow(fields)  # Write the header

        filter_string = {}
        filter_instance = ModelFilter.objects.filter(parent=aPath.lower())
        for filter_data in filter_instance:
            filter_string[f'{filter_data.key}__icontains'] = filter_data.value

        order_by = request.GET.get('order_by', 'id')
        queryset = aModelClass.objects.filter(**filter_string).order_by(order_by)

        items = user_filter(request, queryset, db_field_names)

        for item in items:
            row_data = []
            for field in fields:
                try:
                    row_data.append(getattr(item, field))
                except AttributeError:
                    row_data.append('') 
            writer.writerow(row_data)

        return response


@login_required
def registro(request):
    """Vista para el registro de movimientos de caja"""
    
    # Handle AJAX requests
    if request.method == 'GET' and request.GET.get('ajax') == 'true':
        caja_id = request.GET.get('caja_id')
        
        if request.GET.get('get_turnos') == 'true':
            # Return turnos for the selected caja
            if caja_id:
                turnos = Turno.objects.filter(caja_id=caja_id).values('id', 'nombre')
                return JsonResponse({
                    'success': True,
                    'turnos': list(turnos)
                })
            return JsonResponse({'success': False, 'error': 'No se especificó una caja'})
        
        if not caja_id:
            return JsonResponse({'success': False, 'error': 'No se especificó una caja'})
        
        try:
            caja = get_object_or_404(Caja, id=caja_id)
            # Ordenar por ID descendente (más recientes primero) como orden por defecto
            movimientos = MovimientoCaja.objects.filter(caja=caja).order_by('-id')
            
            # Prepare movements data for JSON response
            movimientos_data = []
            for mov in movimientos:
                movimientos_data.append({
                    'id': mov.id,
                    'fecha': mov.fecha.strftime('%Y-%m-%d'),
                    'fecha_completa': mov.fecha.strftime('%Y-%m-%d %H:%M:%S'),
                    'fecha_display': mov.fecha.strftime('%d/%m/%Y %H:%M'),
                    'datetime_iso': mov.fecha.isoformat(),
                    'turno': str(mov.turno),
                    'concepto': str(mov.concepto),
                    'cantidad': float(mov.cantidad),
                    'es_gasto': mov.es_gasto(),
                    'justificante': mov.justificante or '',
                    'tiene_archivo': bool(mov.archivo_justificante),
                    'archivo_url': mov.archivo_justificante.url if mov.archivo_justificante else None,
                    'descripcion': mov.descripcion or ''
                })
            
            # Calculate summary
            total_ingresos = sum(mov.cantidad for mov in movimientos if not mov.es_gasto())
            total_gastos = sum(mov.cantidad for mov in movimientos if mov.es_gasto())
            
            resumen = {
                'total_ingresos': float(total_ingresos),
                'total_gastos': float(total_gastos),
                'saldo_actual': float(caja.saldo)
            }
            
            return JsonResponse({
                'success': True,
                'movimientos': movimientos_data,
                'resumen': resumen
            })
            
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    # Handle POST requests (add/delete movements)
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'add':
            try:
                # Create new movement
                caja_id = request.POST.get('caja_id')
                caja = get_object_or_404(Caja, id=caja_id)
                
                # Check if caja is active
                if not caja.activa:
                    return JsonResponse({'success': False, 'error': 'No se pueden añadir movimientos a una caja inactiva'})
                
                # Create movement
                fecha_str = request.POST.get('fecha')
                hora_str = request.POST.get('hora', '12:00')
                
                # Combine date and time
                from datetime import datetime
                fecha_datetime = datetime.strptime(f"{fecha_str} {hora_str}", '%Y-%m-%d %H:%M')
                fecha_datetime = timezone.make_aware(fecha_datetime)
                
                # Get the concepto to check if it's a gasto
                concepto = get_object_or_404(Concepto, id=request.POST.get('concepto'))
                
                movimiento = MovimientoCaja(
                    caja=caja,
                    turno_id=request.POST.get('turno'),
                    concepto=concepto,
                    cantidad=float(request.POST.get('cantidad')),
                    fecha=fecha_datetime,
                    descripcion=request.POST.get('descripcion') or None
                )
                
                # Only set justificante fields if the concepto is a gasto
                if concepto.es_gasto:
                    movimiento.justificante = request.POST.get('justificante') or None
                    # Handle file upload only for gastos
                    if 'archivo_justificante' in request.FILES:
                        movimiento.archivo_justificante = request.FILES['archivo_justificante']
                else:
                    # For ingresos, ensure justificante fields are None
                    movimiento.justificante = None
                    movimiento.archivo_justificante = None
                
                # Validate and save
                movimiento.full_clean()
                movimiento.save()
                
                # Procesar desglose de dinero si se proporciona
                desglose_form = DesgloseDineroForm(request.POST)
                if desglose_form.is_valid():
                    movimientos_dinero_data = desglose_form.get_movimientos_dinero_data()
                    
                    # Validar que el total neto del desglose coincida con la cantidad del movimiento
                    if movimientos_dinero_data:
                        total_neto_desglose = Decimal('0.00')
                        for mov_data in movimientos_dinero_data:
                            cantidad_neta = mov_data['cantidad_entrada'] - mov_data['cantidad_salida']
                            valor_neto = cantidad_neta * mov_data['denominacion'].valor
                            total_neto_desglose += valor_neto
                        
                        # Verificar que coincida con la cantidad del movimiento (con tolerancia de 1 céntimo)
                        diferencia = abs(total_neto_desglose - movimiento.cantidad)
                        if diferencia > Decimal('0.01'):
                            return JsonResponse({
                                'success': False, 
                                'error': f'El desglose de dinero no coincide con la cantidad del movimiento. '
                                        f'Diferencia: {diferencia:.2f}€'
                            })
                    
                    # Crear los movimientos de dinero
                    for mov_data in movimientos_dinero_data:
                        MovimientoDinero.objects.create(
                            movimiento_caja=movimiento,
                            denominacion=mov_data['denominacion'],
                            cantidad_entrada=mov_data['cantidad_entrada'],
                            cantidad_salida=mov_data['cantidad_salida']
                        )
                
                return JsonResponse({'success': True, 'message': 'Movimiento añadido correctamente'})
                
            except Exception as e:
                return JsonResponse({'success': False, 'error': str(e)})
        
        elif action == 'delete':
            try:
                movimiento_id = request.POST.get('movimiento_id')
                movimiento = get_object_or_404(MovimientoCaja, id=movimiento_id)
                movimiento.delete()
                
                return JsonResponse({'success': True, 'message': 'Movimiento eliminado correctamente'})
                
            except Exception as e:
                return JsonResponse({'success': False, 'error': str(e)})
    
    # GET request - render the template
    cajas = Caja.objects.all().order_by('-año', 'nombre')
    # Only get turnos for active cajas initially
    turnos = Turno.objects.filter(caja__activa=True)
    conceptos = Concepto.objects.all()
    # Get denominaciones for the money breakdown form
    denominaciones = DenominacionEuro.objects.filter(activa=True).order_by('-valor')
    
    context = {
        'cajas': cajas,
        'turnos': turnos,
        'conceptos': conceptos,
        'denominaciones': denominaciones,
        'segment': 'registro'
    }
    
    return render(request, 'pages/registro.html', context)

@login_required
def saldo(request):
    """Vista para mostrar el estado económico detallado de la caja seleccionada"""
    
    # Get all cajas for the selector
    cajas = Caja.objects.all().order_by('-año', 'nombre')
    
    # Handle AJAX requests for chart data
    if request.method == 'GET' and request.GET.get('ajax') == 'true':
        caja_id = request.GET.get('caja_id')
        
        if not caja_id:
            return JsonResponse({'success': False, 'error': 'No se especificó una caja'})
        
        try:
            caja = get_object_or_404(Caja, id=caja_id)
            movimientos = MovimientoCaja.objects.filter(caja=caja).order_by('fecha')
            
            # Prepare data for charts
            monthly_data = {}
            daily_data = {}
            concept_data = {}
            balance_evolution = []
            
            running_balance = caja.saldo  # Start with the current balance of the caja
            
            for mov in movimientos:
                month_key = mov.fecha.strftime('%Y-%m')
                day_key = mov.fecha.strftime('%Y-%m-%d')
                concept_key = str(mov.concepto)
                
                # Monthly aggregation
                if month_key not in monthly_data:
                    monthly_data[month_key] = {'ingresos': 0, 'gastos': 0}
                
                if mov.es_gasto():
                    monthly_data[month_key]['gastos'] += float(mov.cantidad)
                else:
                    monthly_data[month_key]['ingresos'] += float(mov.cantidad)
                
                # Concept aggregation
                if concept_key not in concept_data:
                    concept_data[concept_key] = {'total': 0, 'tipo': 'gasto' if mov.es_gasto() else 'ingreso'}
                concept_data[concept_key]['total'] += float(mov.cantidad)
                
                # Balance evolution
                running_balance += mov.cantidad_real()
                balance_evolution.append({
                    'fecha': mov.fecha.strftime('%Y-%m-%d'),
                    'balance': float(running_balance),
                    'movimiento': float(mov.cantidad_real())
                })
            
            # Calculate totals
            total_ingresos = sum(mov.cantidad for mov in movimientos if not mov.es_gasto())
            total_gastos = sum(mov.cantidad for mov in movimientos if mov.es_gasto())
            
            # Recent movements (last 10)
            recent_movements = []
            for mov in movimientos.order_by('-fecha')[:10]:
                recent_movements.append({
                    'fecha': mov.fecha.strftime('%d/%m/%Y %H:%M'),
                    'concepto': str(mov.concepto),
                    'cantidad': float(mov.cantidad),
                    'es_gasto': mov.es_gasto(),
                    'turno': str(mov.turno)
                })
            
            # Get current money breakdown for the caja
            desglose_actual = []
            for desglose in caja.obtener_desglose_actual():
                if desglose.cantidad > 0:  # Solo mostrar denominaciones con cantidad > 0
                    desglose_actual.append({
                        'denominacion': str(desglose.denominacion),
                        'valor': float(desglose.denominacion.valor),
                        'cantidad': desglose.cantidad,
                        'valor_total': float(desglose.valor_total()),
                        'es_billete': desglose.denominacion.es_billete
                    })
            
            return JsonResponse({
                'success': True,
                'caja_info': {
                    'nombre': caja.nombre,
                    'año': caja.año,
                    'saldo_actual': float(caja.saldo)
                },
                'totals': {
                    'total_ingresos': float(total_ingresos),
                    'total_gastos': float(total_gastos),
                    'saldo_actual': float(caja.saldo),
                    'total_movimientos': movimientos.count()
                },
                'monthly_data': monthly_data,
                'concept_data': concept_data,
                'balance_evolution': balance_evolution,
                'recent_movements': recent_movements,
                'desglose_actual': desglose_actual
            })
            
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    # GET request - render the template
    context = {
        'cajas': cajas,
        'segment': 'saldo'
    }
    
    return render(request, 'pages/saldo.html', context)

@login_required
def tables(request):
    """Vista para mostrar tablas de resultados por conceptos y turnos"""
    
    # Get all cajas for the selector
    cajas = Caja.objects.all().order_by('-año', 'nombre')
    
    # Handle AJAX requests for table data
    if request.method == 'GET' and request.GET.get('ajax') == 'true':
        caja_id = request.GET.get('caja_id')
        
        if not caja_id:
            return JsonResponse({'success': False, 'error': 'No se especificó una caja'})
        
        try:
            caja = get_object_or_404(Caja, id=caja_id)
            movimientos = MovimientoCaja.objects.filter(caja=caja)
            
            # Prepare data for conceptos table
            conceptos_data = []
            conceptos_dict = {}
            
            for mov in movimientos:
                concepto_nombre = str(mov.concepto)
                if concepto_nombre not in conceptos_dict:
                    conceptos_dict[concepto_nombre] = {
                        'nombre': concepto_nombre,
                        'es_gasto': mov.concepto.es_gasto,
                        'total': 0,
                        'count': 0
                    }
                
                conceptos_dict[concepto_nombre]['total'] += float(mov.cantidad)
                conceptos_dict[concepto_nombre]['count'] += 1
            
            conceptos_data = list(conceptos_dict.values())
            conceptos_data.sort(key=lambda x: x['nombre'])
            
            # Prepare data for turnos table
            turnos_data = []
            turnos_dict = {}
            
            for mov in movimientos:
                turno_nombre = str(mov.turno)
                if turno_nombre not in turnos_dict:
                    turnos_dict[turno_nombre] = {
                        'nombre': turno_nombre,
                        'ingresos': 0,
                        'gastos': 0,
                        'count': 0
                    }
                
                if mov.es_gasto():
                    turnos_dict[turno_nombre]['gastos'] += float(mov.cantidad)
                else:
                    turnos_dict[turno_nombre]['ingresos'] += float(mov.cantidad)
                
                turnos_dict[turno_nombre]['count'] += 1
            
            turnos_data = list(turnos_dict.values())
            turnos_data.sort(key=lambda x: x['nombre'])
            
            return JsonResponse({
                'success': True,
                'caja_info': {
                    'nombre': caja.nombre,
                    'año': caja.año,
                    'saldo_actual': float(caja.saldo)
                },
                'conceptos': conceptos_data,
                'turnos': turnos_data
            })
            
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    # GET request - render the template
    context = {
        'cajas': cajas,
        'segment': 'tables'
    }
    
    return render(request, 'pages/tables.html', context)