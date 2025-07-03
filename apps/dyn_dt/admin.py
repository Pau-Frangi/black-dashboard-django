from django.contrib import admin
from .models import *

# Register your models here.

admin.site.register(PageItems)
admin.site.register(HideShowFilter)
admin.site.register(ModelFilter)


@admin.register(Turno)
class TurnoAdmin(admin.ModelAdmin):
    list_display = ('nombre',)
    search_fields = ('nombre',)
    ordering = ('nombre',)


@admin.register(Concepto)
class ConceptoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'es_gasto')
    list_filter = ('es_gasto',)
    search_fields = ('nombre',)
    ordering = ('nombre',)


@admin.register(Caja)
class CajaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'año', 'saldo', 'activa', 'total_movimientos')
    list_filter = ('año', 'activa')
    search_fields = ('nombre',)
    ordering = ('-año', 'nombre')
    readonly_fields = ('saldo',)  # El saldo no se puede modificar manualmente
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('nombre', 'año', 'activa')
        }),
        ('Saldo', {
            'fields': ('saldo',),
            'description': 'El saldo se actualiza automáticamente con los movimientos. '
                          'Solo se puede establecer al crear la caja.'
        }),
        ('Observaciones', {
            'fields': ('observaciones',),
            'classes': ('collapse',)
        }),
    )
    
    def total_movimientos(self, obj):
        return obj.movimientos.count()
    total_movimientos.short_description = 'Total movimientos'
    
    actions = ['recalcular_saldos_accion']
    
    def recalcular_saldos_accion(self, request, queryset):
        """Acción del admin para recalcular saldos de cajas seleccionadas"""
        for caja in queryset:
            caja.recalcular_saldo()
        
        self.message_user(
            request,
            f'Saldos recalculados para {queryset.count()} caja(s)'
        )
    recalcular_saldos_accion.short_description = 'Recalcular saldos de cajas seleccionadas'
    
    def get_readonly_fields(self, request, obj=None):
        """Hace el campo saldo de solo lectura solo para cajas existentes"""
        if obj:  # Editando una caja existente
            return self.readonly_fields + ('saldo',)
        return self.readonly_fields  # Al crear, se permite establecer saldo inicial


@admin.register(MovimientoCaja)
class MovimientoCajaAdmin(admin.ModelAdmin):
    list_display = ('fecha_display', 'caja', 'turno', 'concepto', 'cantidad_display', 'justificante')
    list_filter = ('fecha', 'caja', 'turno', 'concepto__es_gasto')
    search_fields = ('observaciones', 'justificante')
    ordering = ('-fecha',)
    date_hierarchy = 'fecha'
    
    def fecha_display(self, obj):
        return obj.fecha.strftime('%d/%m/%Y %H:%M')
    fecha_display.short_description = 'Fecha y Hora'
    
    def cantidad_display(self, obj):
        signo = "-" if obj.es_gasto() else "+"
        return f"{signo}{obj.cantidad:.2f}€"
    cantidad_display.short_description = 'Cantidad'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('caja', 'turno', 'concepto')
