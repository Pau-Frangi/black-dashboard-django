from django.contrib import admin
from .models import *

# Register your models here.

admin.site.register(PageItems)
admin.site.register(HideShowFilter)
admin.site.register(ModelFilter)


@admin.register(Turno)
class TurnoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'ejercicio', 'ejercicio_año', 'creado_por', 'creado_en')
    list_filter = ('ejercicio', 'ejercicio__año')
    search_fields = ('nombre', 'ejercicio__nombre')
    ordering = ('ejercicio__nombre', 'nombre')
    readonly_fields = ('creado_por', 'creado_en')
    
    def save_model(self, request, obj, form, change):
        if not change:  # Only on creation
            obj.creado_por = request.user
        super().save_model(request, obj, form, change)
    
    def ejercicio_año(self, obj):
        return obj.ejercicio.año
    ejercicio_año.short_description = 'Año del ejercicio'


@admin.register(Concepto)
class ConceptoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'es_gasto', 'creado_por', 'creado_en')
    list_filter = ('es_gasto',)
    search_fields = ('nombre',)
    ordering = ('nombre',)
    readonly_fields = ('creado_por', 'creado_en')

    def save_model(self, request, obj, form, change):
        if not change:  # Only on creation
            obj.creado_por = request.user
        super().save_model(request, obj, form, change)


@admin.register(Caja)
class CajaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'saldo_caja', 'saldo_desglose', 'activa', 'creado_por', 'creado_en')
    list_filter = ('activa',)
    search_fields = ('nombre',)
    ordering = ('-nombre',)
    readonly_fields = ('saldo_caja', 'saldo_desglose', 'creado_por', 'creado_en')  # Los saldos no se pueden modificar manualmente
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('nombre', 'activa')
        }),
        ('Saldos', {
            'fields': ('saldo_caja',),
            'description': 'El saldo se actualiza automáticamente con los movimientos. '
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
    
    def total_turnos_ejercicio(self, obj):
        return obj.ejercicio.turnos.count()
    total_turnos_ejercicio.short_description = 'Turnos (Ejercicio)'
    
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

    def save_model(self, request, obj, form, change):
        if not change:  # Solo en creación
            obj.creado_por = request.user
        super().save_model(request, obj, form, change)


@admin.register(MovimientoCaja)
class MovimientoCajaAdmin(admin.ModelAdmin):
    list_display = ('fecha_display', 'ejercicio', 'caja', 'turno', 'concepto', 'cantidad_display', 'justificante_display', 'tiene_archivo', 'tiene_desglose', 'creado_por', 'creado_en')
    list_filter = ('fecha', 'caja', 'turno', 'concepto__es_gasto', 'ejercicio')
    search_fields = ('descripcion', 'justificante')
    ordering = ('-fecha',)
    date_hierarchy = 'fecha'
    readonly_fields = ('creado_por', 'creado_en')

    fieldsets = (
        ('Información Básica', {
            'fields': ('ejercicio', 'caja', 'turno', 'concepto', 'cantidad', 'fecha')
        }),
        ('Justificante', {
            'fields': ('justificante', 'archivo_justificante')
        }),
        ('Descripción', {
            'fields': ('descripcion',)
        }),
        ('Información de Creación', {
            'fields': ('creado_por', 'creado_en'),
            'classes': ('collapse',)
        }),
    )

    def save_model(self, request, obj, form, change):
        if not change:  # Only on creation
            obj.creado_por = request.user
        super().save_model(request, obj, form, change)
    
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
    list_display = ('fecha_display', 'ejercicio', 'turno', 'concepto', 'cantidad_display', 'referencia_bancaria', 'tiene_archivo', 'creado_por', 'creado_en')
    list_filter = ('fecha', 'concepto__es_gasto', 'ejercicio', 'turno')
    search_fields = ('descripcion', 'referencia_bancaria', 'ejercicio__nombre', 'concepto__nombre', 'turno__nombre')
    ordering = ('-fecha',)
    date_hierarchy = 'fecha'
    readonly_fields = ('creado_por', 'creado_en')

    fieldsets = (
        ('Información Básica', {
            'fields': ('ejercicio', 'turno', 'concepto', 'cantidad', 'fecha', 'referencia_bancaria')
        }),
        ('Descripción', {
            'fields': ('descripcion',)
        }),
        ('Justificante', {
            'fields': ('archivo_justificante',),
            'description': 'Archivo de justificante para el movimiento bancario'
        }),
        ('Información de Creación', {
            'fields': ('creado_por', 'creado_en'),
            'classes': ('collapse',)
        }),
    )

    def save_model(self, request, obj, form, change):
        if not change:  # Only on creation
            obj.creado_por = request.user
        super().save_model(request, obj, form, change)
    
    def fecha_display(self, obj):
        return obj.fecha.strftime('%d/%m/%Y %H:%M')
    fecha_display.short_description = 'Fecha y Hora'
    
    def cantidad_display(self, obj):
        signo = "-" if obj.es_gasto() else "+"
        return f"{signo}{obj.cantidad:.2f}€"
    cantidad_display.short_description = 'Cantidad'
    
    def tiene_archivo(self, obj):
        return "Sí" if obj.archivo_justificante else "No"
    tiene_archivo.short_description = 'Archivo'
    tiene_archivo.boolean = False


@admin.register(DenominacionEuro)
class DenominacionEuroAdmin(admin.ModelAdmin):
    list_display = ('valor', 'es_billete', 'activa', 'creado_por', 'creado_en')
    list_filter = ('es_billete', 'activa')
    ordering = ('-valor',)
    readonly_fields = ('creado_por', 'creado_en')

    def save_model(self, request, obj, form, change):
        if not change:  # Only on creation
            obj.creado_por = request.user
        super().save_model(request, obj, form, change)


@admin.register(DesgloseCaja)
class DesgloseCajaAdmin(admin.ModelAdmin):
    list_display = ('caja', 'denominacion', 'cantidad', 'valor_total', 'get_denominacion_tipo', 'creado_por', 'creado_en')
    list_filter = ('caja', 'denominacion__es_billete')
    ordering = ('caja', '-denominacion__valor')
    readonly_fields = ('valor_total', 'creado_por', 'creado_en')

    def get_denominacion_tipo(self, obj):
        return "Billete" if obj.denominacion.es_billete else "Moneda"
    get_denominacion_tipo.short_description = 'Tipo'

    def save_model(self, request, obj, form, change):
        if not change:  # Solo en creación
            obj.creado_por = request.user
        super().save_model(request, obj, form, change)


@admin.register(MovimientoDinero)
class MovimientoDineroAdmin(admin.ModelAdmin):
    list_display = ('movimiento_caja', 'denominacion', 'cantidad_entrada', 'cantidad_salida', 'cantidad_neta', 'valor_neto', 'creado_por', 'creado_en')
    list_filter = ('denominacion__es_billete', 'denominacion')
    ordering = ('-movimiento_caja__fecha',)
    readonly_fields = ('cantidad_neta', 'valor_neto', 'creado_por', 'creado_en')

    def save_model(self, request, obj, form, change):
        if not change:  # Only on creation
            obj.creado_por = request.user
        super().save_model(request, obj, form, change)


@admin.register(Ejercicio)
class EjercicioAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'año', 'saldo_banco', 'saldo_cajas', 'saldo_total_display', 'activo', 'creado_por', 'creado_en')
    list_filter = ('año', 'activo')
    search_fields = ('nombre',)
    ordering = ('-año', 'nombre')
    readonly_fields = ('saldo_cajas', 'saldo_total_display', 'creado_por', 'creado_en')
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('nombre', 'año', 'activo')
        }),
        ('Saldos', {
            'fields': ('saldo_banco', 'saldo_cajas', 'saldo_total_display'),
            'description': 'El saldo de cajas y total se calculan automáticamente.'
        }),
        ('Descripción', {
            'fields': ('descripcion',),
            'classes': ('collapse',)
        }),
        ('Información de Creación', {
            'fields': ('creado_por', 'creado_en'),
            'classes': ('collapse',)
        }),
    )
    
    def saldo_cajas(self, obj):
        return f"{obj.calcular_saldo_cajas():.2f}€"
    saldo_cajas.short_description = 'Saldo de Cajas'
    
    def saldo_total_display(self, obj):
        return f"{obj.saldo_total:.2f}€"
    saldo_total_display.short_description = 'Saldo Total'
    
    def total_cajas(self, obj):
        return obj.cajas.count()
    total_cajas.short_description = 'Total de Cajas'
    
    actions = ['recalcular_saldos_cajas_accion']
    
    def recalcular_saldos_cajas_accion(self, request, queryset):
        """Acción del admin para recalcular saldos de todas las cajas de los ejercicios seleccionados"""
        total_cajas = 0
        for ejercicio in queryset:
            ejercicio.recalcular_saldos_cajas()
            total_cajas += ejercicio.cajas.count()
        
        self.message_user(
            request,
            f'Saldos recalculados para {total_cajas} caja(s) en {queryset.count()} ejercicio(s)'
        )
    recalcular_saldos_cajas_accion.short_description = 'Recalcular saldos de cajas en ejercicios seleccionados'

    def save_model(self, request, obj, form, change):
        if not change:  # Solo en creación
            obj.creado_por = request.user
        super().save_model(request, obj, form, change)


@admin.register(FormatoMovimientoBanco)
class FormatoMovimientoBancoAdmin(admin.ModelAdmin):
    list_display = ('formato', 'creado_por', 'creado_en')
    list_filter = ('formato',)
    ordering = ('-creado_en',)
    readonly_fields = ('creado_por', 'creado_en')

    def save_model(self, request, obj, form, change):
        if not change:  # Solo en creación
            obj.creado_por = request.user
        super().save_model(request, obj, form, change)
     
        
@admin.register(CuentaBancaria)
class CuentaBancariaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'IBAN', 'activo', 'creado_por', 'creado_en')
    list_filter = ('activo',)
    search_fields = ('nombre', 'IBAN')
    ordering = ('-creado_en',)
    readonly_fields = ('creado_por', 'creado_en')

    def save_model(self, request, obj, form, change):
        if not change:  # Only on creation
            obj.creado_por = request.user
        super().save_model(request, obj, form, change)
        
        
@admin.register(Campamento)
class CampamentoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'creado_por', 'creado_en')
    list_filter = ('nombre',)
    search_fields = ('nombre',)
    readonly_fields = ('creado_por', 'creado_en')

    def save_model(self, request, obj, form, change):
        if not change:
            obj.creado_por = request.user
        super().save_model(request, obj, form, change)