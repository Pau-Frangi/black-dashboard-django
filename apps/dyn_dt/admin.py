from django.contrib import admin
from .models import *

# Register your models here.

admin.site.register(PageItems)
admin.site.register(HideShowFilter)
admin.site.register(ModelFilter)


@admin.register(Turno)
class TurnoAdmin(admin.ModelAdmin):
    list_display = ('campamento', 'nombre', 'ejercicio', 'ejercicio_año', 'creado_por', 'creado_en')
    list_filter = ('ejercicio', 'ejercicio__año', 'campamento')
    search_fields = ('nombre', 'ejercicio__nombre', 'campamento__nombre')
    ordering = ('ejercicio__nombre', 'nombre')
    readonly_fields = ('creado_por', 'creado_en', 'modificado_por', 'modificado_en')
    
    def save_model(self, request, obj, form, change):
        obj.save(user=request.user)
    
    def ejercicio_año(self, obj):
        return obj.ejercicio.año
    ejercicio_año.short_description = 'Año del ejercicio'


@admin.register(Concepto)
class ConceptoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'es_gasto', 'creado_por', 'creado_en')
    list_filter = ('es_gasto',)
    search_fields = ('nombre',)
    ordering = ('nombre',)
    readonly_fields = ('creado_por', 'creado_en', 'modificado_por', 'modificado_en')

    def save_model(self, request, obj, form, change):
        obj.save(user=request.user)


@admin.register(Ejercicio)
class EjercicioAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'año', 'saldo_banco_display', 'saldo_cajas_display', 'saldo_total_display', 'activo', 'creado_por', 'creado_en')
    list_filter = ('año', 'activo')
    search_fields = ('nombre',)
    ordering = ('-año', 'nombre')
    readonly_fields = ('saldo_total_display', 'saldo_banco_display', 'saldo_cajas_display', 'creado_por', 'creado_en', 'modificado_por', 'modificado_en')
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('nombre', 'año', 'activo')
        }),
        ('Saldos', {
            'fields': ('saldo_banco_display', 'saldo_cajas_display', 'saldo_total_display'),
            'description': 'El saldo de cajas y total se calculan automáticamente.'
        }),
        ('Descripción', {
            'fields': ('descripcion',),
            'classes': ('collapse',)
        }),
        ('Información de creación y modificación', {
            'fields': ('creado_por', 'creado_en', 'modificado_por', 'modificado_en'),
            'classes': ('collapse',)
        }),
    )
    
    def saldo_cajas(self, obj):
        return f"{obj.calcular_saldo_cajas():.2f}€"
    saldo_cajas.short_description = 'Saldo de Cajas'
    
    def saldo_banco_display(self, obj):
        return f"{obj.calcular_saldo_banco():.2f}€"
    saldo_banco_display.short_description = 'Saldo de Banco'
    
    def saldo_cajas_display(self, obj):
        return f"{obj.calcular_saldo_cajas():.2f}€"
    saldo_cajas_display.short_description = 'Saldo de Cajas'
    
    def saldo_total_display(self, obj):
        return f"{obj.saldo_total:.2f}€"
    saldo_total_display.short_description = 'Saldo Total'
    
    def total_cajas(self, obj):
        return obj.cajas.count()
    total_cajas.short_description = 'Total de Cajas'
    
    def save_model(self, request, obj, form, change):
        obj.save(user=request.user)
 
        
@admin.register(Campamento)
class CampamentoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'creado_por', 'creado_en')
    list_filter = ('nombre',)
    search_fields = ('nombre',)
    readonly_fields = ('creado_por', 'creado_en', 'modificado_por', 'modificado_en')

    def save_model(self, request, obj, form, change):
        obj.save(user=request.user)