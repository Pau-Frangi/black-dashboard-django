"""
Handlers for dynamic datatable operations.
"""
import json
import csv
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse
from django.urls import reverse
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.conf import settings
from django.views import View
from django.db import models

from apps.dyn_dt.models import ModelFilter, PageItems, HideShowFilter
from apps.dyn_dt.utils import user_filter, get_model_field_names
from cli import name_to_class, get_model_fk_values, get_model_fk


class DatatableHandler:
    """Handles dynamic datatable operations."""
    
    @staticmethod
    def get_model_data(aPath):
        """
        Gets model class and related data for a given path.
        
        Args:
            aPath: Model path string
            
        Returns:
            Tuple of (model_name, model_class) or (None, None) if not found
        """
        if aPath in settings.DYNAMIC_DATATB.keys():
            aModelName = settings.DYNAMIC_DATATB[aPath]
            aModelClass = name_to_class(aModelName)
            return aModelName, aModelClass
        return None, None
    
    @staticmethod
    def prepare_model_context(aModelClass, aPath):
        """
        Prepares context data for model display.
        
        Args:
            aModelClass: Django model class
            aPath: Model path string
            
        Returns:
            Dictionary with model context data
        """
        # Get model fields and relationships
        db_fields = [field.name for field in aModelClass._meta.fields]
        fk_fields = get_model_fk_values(aModelClass)
        
        # Get filterable fields (non-FK fields)
        db_filters = [f for f in db_fields if f not in fk_fields.keys()]
        
        # Get field choices
        choices_dict = {}
        for field in aModelClass._meta.fields:
            if field.choices:
                choices_dict[field.name] = field.choices
        
        # Get field display settings
        field_names = []
        for field_name in db_fields:
            fields, created = HideShowFilter.objects.get_or_create(
                key=field_name, 
                parent=aPath.lower()
            )
            if fields.key in db_fields:
                field_names.append(fields)
        
        # Get field types for proper form rendering
        field_types = {
            'integer_fields': get_model_field_names(aModelClass, models.IntegerField),
            'date_time_fields': get_model_field_names(aModelClass, models.DateTimeField),
            'email_fields': get_model_field_names(aModelClass, models.EmailField),
            'text_fields': get_model_field_names(aModelClass, (models.TextField, models.CharField))
        }
        
        return {
            'db_fields': db_fields,
            'fk_fields': fk_fields,
            'db_filters': db_filters,
            'choices_dict': choices_dict,
            'field_names': field_names,
            'field_types': field_types
        }
    
    @staticmethod
    def apply_filters_and_pagination(request, aModelClass, aPath, db_fields, fk_fields):
        """
        Applies filters and pagination to queryset.
        
        Args:
            request: Django request object
            aModelClass: Django model class
            aPath: Model path string
            db_fields: List of database fields
            fk_fields: Dictionary of foreign key fields
            
        Returns:
            Paginated queryset
        """
        # Apply model filters
        filter_string = {}
        filter_instance = ModelFilter.objects.filter(parent=aPath.lower())
        for filter_data in filter_instance:
            if filter_data.key in db_fields: 
                filter_string[f'{filter_data.key}__icontains'] = filter_data.value
        
        # Apply ordering
        order_by = request.GET.get('order_by', 'id')
        if order_by not in db_fields:
            order_by = 'id'
        
        # Build queryset
        queryset = aModelClass.objects.filter(**filter_string).order_by(order_by)
        item_list = user_filter(request, queryset, db_fields, fk_fields.keys())
        
        # Apply pagination
        page_items = PageItems.objects.filter(parent=aPath.lower()).last()
        p_items = page_items.items_per_page if page_items else 25
        
        page = request.GET.get('page', 1)
        paginator = Paginator(item_list, p_items)
        
        try:
            items = paginator.page(page)
        except (PageNotAnInteger, EmptyPage):
            # Redirect to first page on error
            return None
        
        return items, p_items, filter_instance


class FilterHandler:
    """Handles filter operations for datatables."""
    
    @staticmethod
    def create_filter(request, model_name):
        """
        Creates or updates model filters.
        
        Args:
            request: Django request object
            model_name: Model name string
            
        Returns:
            Redirect response
        """
        model_name = model_name.lower()
        if request.method == "POST":
            keys = request.POST.getlist('key')
            values = request.POST.getlist('value')
            
            for key, value in zip(keys, values):
                ModelFilter.objects.update_or_create(
                    parent=model_name,
                    key=key,
                    defaults={'value': value}
                )
        
        return redirect(reverse('model_dt', args=[model_name]))
    
    @staticmethod
    def delete_filter(request, model_name, filter_id):
        """
        Deletes a specific filter.
        
        Args:
            request: Django request object
            model_name: Model name string
            filter_id: Filter ID to delete
            
        Returns:
            Redirect response
        """
        model_name = model_name.lower()
        filter_instance = get_object_or_404(
            ModelFilter, 
            id=filter_id, 
            parent=model_name
        )
        filter_instance.delete()
        return redirect(reverse('model_dt', args=[model_name]))
    
    @staticmethod
    def create_hide_show_filter(request, model_name):
        """
        Creates or updates field visibility filters.
        
        Args:
            request: Django request object
            model_name: Model name string
            
        Returns:
            JsonResponse with result
        """
        model_name = model_name.lower()
        if request.method == "POST":
            try:
                data_str = list(request.POST.keys())[0]
                data = json.loads(data_str)
                
                HideShowFilter.objects.update_or_create(
                    parent=model_name,
                    key=data.get('key'),
                    defaults={'value': data.get('value')}
                )
                
                return JsonResponse({'message': 'Model updated successfully'})
            except (json.JSONDecodeError, IndexError, KeyError):
                return JsonResponse({'error': 'Invalid request data'}, status=400)
        
        return JsonResponse({'error': 'Invalid request'}, status=400)
    
    @staticmethod
    def create_page_items(request, model_name):
        """
        Updates pagination settings for a model.
        
        Args:
            request: Django request object
            model_name: Model name string
            
        Returns:
            Redirect response
        """
        model_name = model_name.lower()
        if request.method == 'POST':
            items = request.POST.get('items')
            PageItems.objects.update_or_create(
                parent=model_name,
                defaults={'items_per_page': items}
            )
        return redirect(reverse('model_dt', args=[model_name]))


class CRUDHandler:
    """Handles CRUD operations for datatables."""
    
    @staticmethod
    def create_item(request, aPath):
        """
        Creates a new model instance.
        
        Args:
            request: Django request object
            aPath: Model path string
            
        Returns:
            Redirect response
        """
        _, aModelClass = DatatableHandler.get_model_data(aPath)
        if not aModelClass:
            return HttpResponse(f' > ERR: Getting ModelClass for path: {aPath}')
        
        if request.method == 'POST':
            data = {}
            fk_fields = get_model_fk(aModelClass)
            
            for attribute, value in request.POST.items():
                if attribute == 'csrfmiddlewaretoken':
                    continue
                
                # Process foreign keys
                if attribute in fk_fields.keys():
                    value = name_to_class(fk_fields[attribute]).objects.filter(
                        id=value
                    ).first()
                
                data[attribute] = value if value else ''
            
            aModelClass.objects.create(**data)
        
        return redirect(request.META.get('HTTP_REFERER'))
    
    @staticmethod
    def update_item(request, aPath, item_id):
        """
        Updates an existing model instance.
        
        Args:
            request: Django request object
            aPath: Model path string
            item_id: ID of item to update
            
        Returns:
            Redirect response
        """
        _, aModelClass = DatatableHandler.get_model_data(aPath)
        if not aModelClass:
            return HttpResponse(f' > ERR: Getting ModelClass for path: {aPath}')
        
        item = get_object_or_404(aModelClass, id=item_id)
        fk_fields = get_model_fk(aModelClass)
        
        if request.method == 'POST':
            for attribute, value in request.POST.items():
                if attribute == 'csrfmiddlewaretoken':
                    continue
                
                if getattr(item, attribute, value) is not None:
                    # Process foreign keys
                    if attribute in fk_fields.keys():
                        value = name_to_class(fk_fields[attribute]).objects.filter(
                            id=value
                        ).first()
                    
                    setattr(item, attribute, value)
            
            item.save()
        
        return redirect(request.META.get('HTTP_REFERER'))
    
    @staticmethod
    def delete_item(request, aPath, item_id):
        """
        Deletes a model instance.
        
        Args:
            request: Django request object
            aPath: Model path string
            item_id: ID of item to delete
            
        Returns:
            Redirect response
        """
        _, aModelClass = DatatableHandler.get_model_data(aPath)
        if not aModelClass:
            return HttpResponse(f' > ERR: Getting ModelClass for path: {aPath}')
        
        item = get_object_or_404(aModelClass, id=item_id)
        item.delete()
        return redirect(request.META.get('HTTP_REFERER'))


class ExportHandler:
    """Handles data export operations."""
    
    @staticmethod
    def export_csv(request, aPath):
        """
        Exports model data as CSV.
        
        Args:
            request: Django request object
            aPath: Model path string
            
        Returns:
            CSV HttpResponse
        """
        _, aModelClass = DatatableHandler.get_model_data(aPath)
        if not aModelClass:
            return HttpResponse(f' > ERR: Getting ModelClass for path: {aPath}')
        
        # Get visible fields
        db_field_names = [field.name for field in aModelClass._meta.get_fields()]
        fields = []
        show_fields = HideShowFilter.objects.filter(value=False, parent=aPath.lower())
        
        for field in show_fields:
            if field.key in db_field_names:
                fields.append(field.key)
        
        # Create CSV response
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="{aPath.lower()}.csv"'
        
        writer = csv.writer(response)
        writer.writerow(fields)  # Write header
        
        # Apply filters and export data
        filter_string = {}
        filter_instance = ModelFilter.objects.filter(parent=aPath.lower())
        for filter_data in filter_instance:
            filter_string[f'{filter_data.key}__icontains'] = filter_data.value
        
        order_by = request.GET.get('order_by', 'id')
        queryset = aModelClass.objects.filter(**filter_string).order_by(order_by)
        items = user_filter(request, queryset, db_field_names)
        
        # Write data rows
        for item in items:
            row_data = []
            for field in fields:
                try:
                    row_data.append(getattr(item, field))
                except AttributeError:
                    row_data.append('')
            writer.writerow(row_data)
        
        return response
