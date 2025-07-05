from django.contrib import admin
from .models import *

# Register your models here.

admin.site.register(PageItems)
admin.site.register(HideShowFilter)
admin.site.register(ModelFilter)


@admin.register(Turno)
class TurnoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'caja', 'caja_año')
    list_filter = ('caja', 'caja__año')
    search_fields = ('nombre', 'caja__nombre')
    ordering = ('caja__nombre', 'nombre')
    
    def caja_año(self, obj):
        return obj.caja.año
    caja_año.short_description = 'Año de la caja'


@admin.register(Concepto)
class ConceptoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'es_gasto')
    list_filter = ('es_gasto',)
    search_fields = ('nombre',)
    ordering = ('nombre',)


@admin.register(Caja)
class CajaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'año', 'saldo', 'saldo_desglose', 'activa', 'total_movimientos', 'total_turnos')
    list_filter = ('año', 'activa')
    search_fields = ('nombre',)
    ordering = ('-año', 'nombre')
    readonly_fields = ('saldo', 'saldo_desglose')  # El saldo no se puede modificar manualmente
    
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
    
    def total_turnos(self, obj):
        return obj.turnos.count()
    total_turnos.short_description = 'Total turnos'
    
    def saldo_desglose(self, obj):
        saldo_calc = obj.calcular_saldo_desde_desglose()
        if saldo_calc != obj.saldo:
            return f"{saldo_calc:.2f}€ ⚠️"
        return f"{saldo_calc:.2f}€ ✓"
    saldo_desglose.short_description = 'Saldo desde desglose'
    
    actions = ['recalcular_saldos_accion', 'recalcular_desglose_accion']
    
    def recalcular_saldos_accion(self, request, queryset):
        """Acción del admin para recalcular saldos de cajas seleccionadas"""
        for caja in queryset:
            caja.recalcular_saldo()
        
        self.message_user(
            request,
            f'Saldos recalculados para {queryset.count()} caja(s)'
        )
    recalcular_saldos_accion.short_description = 'Recalcular saldos de cajas seleccionadas'
    
    def recalcular_desglose_accion(self, request, queryset):
        """Acción del admin para recalcular desglose de cajas seleccionadas"""
        for caja in queryset:
            caja.recalcular_desglose_completo()
        
        self.message_user(
            request,
            f'Desglose recalculado para {queryset.count()} caja(s)'
        )
    recalcular_desglose_accion.short_description = 'Recalcular desglose de cajas seleccionadas'
    
    def get_readonly_fields(self, request, obj=None):
        """Hace el campo saldo de solo lectura solo para cajas existentes"""
        if obj:  # Editando una caja existente
            return self.readonly_fields + ('saldo',)
        return self.readonly_fields  # Al crear, se permite establecer saldo inicial


@admin.register(MovimientoCaja)
class MovimientoCajaAdmin(admin.ModelAdmin):
    list_display = ('fecha_display', 'caja', 'turno', 'concepto', 'cantidad_display', 'justificante_display', 'tiene_archivo')
    list_filter = ('fecha', 'caja', 'turno', 'concepto__es_gasto')
    search_fields = ('descripcion', 'justificante')
    ordering = ('-fecha',)
    date_hierarchy = 'fecha'
    
    def fecha_display(self, obj):
        return obj.fecha.strftime('%d/%m/%Y %H:%M')
    fecha_display.short_description = 'Fecha y Hora'
    
    def cantidad_display(self, obj):
        signo = "-" if obj.es_gasto() else "+"
        return f"{signo}{obj.cantidad:.2f}€"
    cantidad_display.short_description = 'Cantidad'
    
    def justificante_display(self, obj):
        if obj.es_gasto():
            return obj.justificante or "Sin justificante"
        return "N/A (Ingreso)"
    justificante_display.short_description = 'Justificante'
    
    def tiene_archivo(self, obj):
        if obj.es_gasto():
            return "Sí" if obj.archivo_justificante else "No"
        return "N/A"
    tiene_archivo.short_description = 'Archivo'
    tiene_archivo.boolean = False
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('caja', 'turno', 'concepto')


@admin.register(DenominacionEuro)
class DenominacionEuroAdmin(admin.ModelAdmin):
    list_display = ('valor', 'es_billete', 'activa')
    list_filter = ('es_billete', 'activa')
    ordering = ('-valor',)


@admin.register(DesgloseCaja)
class DesgloseCajaAdmin(admin.ModelAdmin):
    list_display = ('caja', 'denominacion', 'cantidad', 'valor_total')
    list_filter = ('caja', 'denominacion__es_billete')
    ordering = ('caja', '-denominacion__valor')
    readonly_fields = ('valor_total',)


@admin.register(MovimientoDinero)
class MovimientoDineroAdmin(admin.ModelAdmin):
    list_display = ('movimiento_caja', 'denominacion', 'cantidad_entrada', 'cantidad_salida', 'cantidad_neta', 'valor_neto')
    list_filter = ('denominacion__es_billete', 'denominacion')
    ordering = ('-movimiento_caja__fecha',)
    readonly_fields = ('cantidad_neta', 'valor_neto')
