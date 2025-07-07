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
    list_display = ('nombre', 'año', 'saldo_caja', 'saldo_banco', 'saldo', 'saldo_desglose', 'activa', 'total_movimientos_caja', 'total_movimientos_banco', 'total_turnos')
    list_filter = ('año', 'activa')
    search_fields = ('nombre',)
    ordering = ('-año', 'nombre')
    readonly_fields = ('saldo_caja', 'saldo_banco', 'saldo', 'saldo_desglose')  # Los saldos no se pueden modificar manualmente
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('nombre', 'año', 'activa')
        }),
        ('Saldos', {
            'fields': ('saldo_caja', 'saldo_banco', 'saldo'),
            'description': 'Los saldos se actualizan automáticamente con los movimientos. '
                          'Solo se pueden establecer al crear la caja.'
        }),
        ('Observaciones', {
            'fields': ('observaciones',),
            'classes': ('collapse',)
        }),
    )
    
    def total_movimientos_caja(self, obj):
        return obj.movimientos.count()
    total_movimientos_caja.short_description = 'Mov. Caja'
    
    def total_movimientos_banco(self, obj):
        return obj.movimientos_banco.count()
    total_movimientos_banco.short_description = 'Mov. Banco'
    
    def total_turnos(self, obj):
        return obj.turnos.count()
    total_turnos.short_description = 'Total turnos'
    
    def saldo_desglose(self, obj):
        saldo_calc = obj.calcular_saldo_desde_desglose()
        if saldo_calc != obj.saldo_caja:
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
        """Hace los campos de saldo de solo lectura solo para cajas existentes"""
        if obj:  # Editando una caja existente
            return self.readonly_fields
        return ('saldo_desglose',)  # Al crear, se permite establecer saldos iniciales


@admin.register(MovimientoCaja)
class MovimientoCajaAdmin(admin.ModelAdmin):
    list_display = ('fecha_display', 'caja', 'turno', 'concepto', 'cantidad_display', 'justificante_display', 'tiene_archivo', 'tiene_desglose')
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
    
    def tiene_desglose(self, obj):
        count = obj.movimientos_dinero.count()
        if count > 0:
            return f"✅ ({count})"
        return "❌ Sin desglose"
    tiene_desglose.short_description = 'Desglose'


@admin.register(MovimientoBanco)
class MovimientoBancoAdmin(admin.ModelAdmin):
    list_display = ('fecha_display', 'caja', 'turno', 'concepto', 'cantidad_display', 'referencia_bancaria', 'justificante_display', 'tiene_archivo')
    list_filter = ('fecha', 'caja', 'turno', 'concepto__es_gasto')
    search_fields = ('descripcion', 'justificante', 'referencia_bancaria')
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


@admin.register(DenominacionEuro)
class DenominacionEuroAdmin(admin.ModelAdmin):
    list_display = ('valor', 'es_billete', 'activa')
    list_filter = ('es_billete', 'activa')
    ordering = ('-valor',)


@admin.register(DesgloseCaja)
class DesgloseCajaAdmin(admin.ModelAdmin):
    list_display = ('caja', 'denominacion', 'cantidad', 'valor_total', 'denominacion_tipo')
    list_filter = ('caja', 'denominacion__es_billete')
    ordering = ('caja', '-denominacion__valor')
    readonly_fields = ('valor_total',)
    search_fields = ('caja__nombre',)
    
    def denominacion_tipo(self, obj):
        return "Billete" if obj.denominacion.es_billete else "Moneda"
    denominacion_tipo.short_description = 'Tipo'
    
    def save_model(self, request, obj, form, change):
        """Guarda el modelo y muestra mensaje sobre actualización de saldo"""
        saldo_anterior = obj.caja.saldo
        super().save_model(request, obj, form, change)
        
        # Recargar la caja para obtener el saldo actualizado
        obj.caja.refresh_from_db()
        saldo_nuevo = obj.caja.saldo
        
        if saldo_anterior != saldo_nuevo:
            self.message_user(
                request,
                f'Desglose guardado. Saldo de {obj.caja.nombre} actualizado de {saldo_anterior:.2f}€ a {saldo_nuevo:.2f}€'
            )
        else:
            self.message_user(request, 'Desglose guardado correctamente')
    
    def delete_model(self, request, obj):
        """Elimina el modelo y muestra mensaje sobre actualización de saldo"""
        caja_nombre = obj.caja.nombre
        saldo_anterior = obj.caja.saldo
        
        super().delete_model(request, obj)
        
        # Recargar la caja para obtener el saldo actualizado
        obj.caja.refresh_from_db()
        saldo_nuevo = obj.caja.saldo
        
        if saldo_anterior != saldo_nuevo:
            self.message_user(
                request,
                f'Desglose eliminado. Saldo de {caja_nombre} actualizado de {saldo_anterior:.2f}€ a {saldo_nuevo:.2f}€'
            )
        else:
            self.message_user(request, 'Desglose eliminado correctamente')
    
    actions = ['recalcular_saldos_desde_desglose']
    
    def recalcular_saldos_desde_desglose(self, request, queryset):
        """Acción para recalcular saldos de cajas basándose en su desglose"""
        cajas_actualizadas = set()
        
        for desglose in queryset:
            if desglose.caja not in cajas_actualizadas:
                saldo_anterior = desglose.caja.saldo
                nuevo_saldo = desglose.caja.calcular_saldo_desde_desglose()
                
                if saldo_anterior != nuevo_saldo:
                    desglose.caja.saldo = nuevo_saldo
                    desglose.caja.save(skip_validation=True)
                
                cajas_actualizadas.add(desglose.caja)
        
        self.message_user(
            request,
            f'Saldos recalculados para {len(cajas_actualizadas)} caja(s) basándose en su desglose'
        )
    recalcular_saldos_desde_desglose.short_description = 'Recalcular saldos desde desglose'


@admin.register(MovimientoDinero)
class MovimientoDineroAdmin(admin.ModelAdmin):
    list_display = ('movimiento_caja', 'denominacion', 'cantidad_entrada', 'cantidad_salida', 'cantidad_neta', 'valor_neto')
    list_filter = ('denominacion__es_billete', 'denominacion')
    ordering = ('-movimiento_caja__fecha',)
    readonly_fields = ('cantidad_neta', 'valor_neto')
