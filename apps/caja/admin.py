from django.contrib import admin
from .models import *
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html


@admin.register(MovimientoCajaIngreso)
class MovimientoCajaIngresoAdmin(admin.ModelAdmin):
    list_display = ('fecha_display', 'ejercicio', 'caja', 'turno', 'concepto', 'importe_display', 'descripcion', 'archivo_display', 'creado_por', 'creado_en')
    search_fields = ('caja__nombre', 'concepto__nombre')
    list_filter = ('fecha', 'caja', 'turno', 'ejercicio', 'creado_por', 'creado_en', 'concepto')
    ordering = ('-fecha',)
    readonly_fields = ('creado_por', 'creado_en', 'modificado_por', 'modificado_en')
    
    
    fieldsets = (
        ('Información básica', {
            'fields': ('fecha', 'ejercicio', 'caja', 'turno', 'concepto', 'importe')
        }),
        ('Archivos adjuntos', {
            'fields': ('archivo',)
        }),
        ('Descripción', {
            'fields': ('descripcion',)
        }),
        ('Información de creación y modificación', {
            'fields': ('creado_por', 'creado_en', 'modificado_por', 'modificado_en')
        }),
        )
 
    def fecha_display(self, obj):
        return obj.fecha.strftime('%d/%m/%Y %H:%M')
    fecha_display.short_description = 'Fecha y Hora'
    
    def archivo_display(self, obj):
        # Si tienes archivo adjunto, muestra un enlace para descargarlo con su nombre
        if obj.archivo:
            return format_html('<a href="{}"> {obj.archivo.name} </a>', obj.archivo.url)
        return 'Sin archivo'
    
    def importe_display(self, obj):
        return f"+ {obj.importe:.2f} €"
 
    def save_model(self, request, obj, form, change):
        obj.save(user=request.user)
        
        
        
@admin.register(MovimientoCajaGasto)
class MovimientoCajaGastoAdmin(admin.ModelAdmin):
    list_display = ('fecha_display', 'ejercicio', 'caja', 'turno', 'concepto', 'importe_display', 'descripcion', 'archivo_display', 'creado_por', 'creado_en')
    search_fields = ('caja__nombre', 'concepto__nombre')
    list_filter = ('fecha', 'caja', 'turno', 'ejercicio', 'creado_por', 'creado_en', 'concepto')
    ordering = ('-fecha',)
    readonly_fields = ('creado_por', 'creado_en', 'modificado_por', 'modificado_en')
    
    fieldsets = (
        ('Información básica', {
            'fields': ('fecha', 'ejercicio', 'caja', 'turno', 'concepto', 'importe')
        }),
        ('Archivos adjuntos', {
            'fields': ('archivo',)
        }),
        ('Descripción', {
            'fields': ('descripcion',)
        }),
        ('Información de creación y modificación', {
            'fields': ('creado_por', 'creado_en', 'modificado_por', 'modificado_en')
        }),
    )
 
    def fecha_display(self, obj):
        return obj.fecha.strftime('%d/%m/%Y %H:%M')
    fecha_display.short_description = 'Fecha y Hora'
    
    def archivo_display(self, obj):
        if obj.archivo:
            return format_html('<a href="{}"> {obj.archivo.name} </a>', obj.archivo.url)
        return 'Sin archivo'
    
    def importe_display(self, obj):
        return f"- {obj.importe:.2f} €"
 
    def save_model(self, request, obj, form, change):
        obj.save(user=request.user)
        

@admin.register(MovimientoCajaTransferencia)
class MovimientoCajaTransferenciaAdmin(admin.ModelAdmin):
    list_display = ('fecha_display', 'ejercicio', 'caja_origen', 'caja_destino', 'turno', 'importe_display', 'descripcion', 'creado_por', 'creado_en')
    search_fields = ('caja_origen__nombre', 'caja_destino__nombre')
    list_filter = ('fecha', 'caja_origen', 'caja_destino', 'turno', 'ejercicio', 'creado_por', 'creado_en')
    ordering = ('-fecha',)
    readonly_fields = ('creado_por', 'creado_en', 'modificado_por', 'modificado_en')

    fieldsets = (
        ('Información básica', {
            'fields': ('fecha', 'ejercicio', 'caja', 'turno', 'importe', 'caja_destino')
        }),
        ('Descripción', {
            'fields': ('descripcion',)
        }),
        ('Información de creación y modificación', {
            'fields': ('creado_por', 'creado_en', 'modificado_por', 'modificado_en')
        }),
    )
 
    def fecha_display(self, obj):
        return obj.fecha.strftime('%d/%m/%Y %H:%M')
    fecha_display.short_description = 'Fecha y Hora'
    
    def importe_display(self, obj):
        return f"{obj.importe:.2f} €"
 
    def save_model(self, request, obj, form, change):
        obj.save(user=request.user)
        
        
@admin.register(MovimientoCajaDeposito)
class MovimientoCajaDepositoAdmin(admin.ModelAdmin):
    list_display = ('fecha_display', 'ejercicio', 'caja', 'turno', 'importe_display', 'descripcion', 'creado_por', 'creado_en')
    search_fields = ('caja__nombre',)
    list_filter = ('fecha', 'caja', 'turno', 'ejercicio', 'creado_por', 'creado_en')
    ordering = ('-fecha',)
    readonly_fields = ('creado_por', 'creado_en', 'modificado_por', 'modificado_en')

    fieldsets = (
        ('Información básica', {
            'fields': ('fecha', 'ejercicio', 'caja', 'turno', 'importe')
        }),
        ('Descripción', {
            'fields': ('descripcion',)
        }),
        ('Información de creación y modificación', {
            'fields': ('creado_por', 'creado_en', 'modificado_por', 'modificado_en')
        }),
    )
 
    def fecha_display(self, obj):
        return obj.fecha.strftime('%d/%m/%Y %H:%M')
    fecha_display.short_description = 'Fecha y Hora'
    
    def importe_display(self, obj):
        return f"{obj.importe:.2f} €"
 
    def save_model(self, request, obj, form, change):
        obj.save(user=request.user)
        
        
@admin.register(MovimientoCajaRetirada)
class MovimientoCajaRetiradaAdmin(admin.ModelAdmin):
    list_display = ('fecha_display', 'ejercicio', 'caja', 'turno', 'importe_display', 'descripcion', 'retirado_por', 'creado_por', 'creado_en')
    search_fields = ('caja__nombre',)
    list_filter = ('fecha', 'caja', 'turno', 'ejercicio', 'creado_por', 'creado_en')
    ordering = ('-fecha',)
    readonly_fields = ('creado_por', 'creado_en', 'modificado_por', 'modificado_en')

    fieldsets = (
        ('Información básica', {
            'fields': ('fecha', 'ejercicio', 'caja', 'turno', 'importe', 'retirado_por')
        }),
        ('Descripción', {
            'fields': ('descripcion',)
        }),
        ('Información de creación y modificación', {
            'fields': ('creado_por', 'creado_en', 'modificado_por', 'modificado_en')
        }),
    )
 
    def fecha_display(self, obj):
        return obj.fecha.strftime('%d/%m/%Y %H:%M')
    fecha_display.short_description = 'Fecha y Hora'
    
    def importe_display(self, obj):
        return f"- {obj.importe:.2f} €"
 
    def save_model(self, request, obj, form, change):
        obj.save(user=request.user)
        
        
@admin.register(DesgloseCaja)
class DesgloseCajaAdmin(admin.ModelAdmin):
    list_display = ('caja', 'denominacion', 'cantidad', 'valor_total', 'get_denominacion_tipo', 'creado_por', 'creado_en')
    list_filter = ('caja', 'denominacion__es_billete')
    ordering = ('caja', '-denominacion__valor')
    readonly_fields = ('valor_total', 'creado_por', 'creado_en', 'modificado_por', 'modificado_en')

    def get_denominacion_tipo(self, obj):
        return "Billete" if obj.denominacion.es_billete else "Moneda"
    get_denominacion_tipo.short_description = 'Tipo'

    def save_model(self, request, obj, form, change):
        obj.save(user=request.user)
        
        
@admin.register(DenominacionEuro)
class DenominacionEuroAdmin(admin.ModelAdmin):
    list_display = ('valor', 'es_billete', 'activa', 'creado_por', 'creado_en')
    list_filter = ('es_billete', 'activa')
    ordering = ('-valor',)
    readonly_fields = ('creado_por', 'creado_en', 'modificado_por', 'modificado_en')

    def save_model(self, request, obj, form, change):
        obj.save(user=request.user)
        
        
@admin.register(MovimientoEfectivo)
class MovimientoEfectivoAdmin(admin.ModelAdmin):
    list_display = (
        'get_movimiento_caja_display',
        'denominacion', 'cantidad_entrada', 'cantidad_salida',
        'cantidad_neta_display', 'importe_neto_display', 'creado_por', 'creado_en',
    )
    list_filter = ('denominacion__es_billete', 'denominacion')
    ordering = ('-creado_en',)
    readonly_fields = ('cantidad_neta_display', 'importe_neto_display', 'creado_por', 'creado_en', 'modificado_por', 'modificado_en')

    def get_movimiento_caja_display(self, obj):
        # Return a string representation of the related object
        if obj.movimiento_caja:
            return str(obj.movimiento_caja)
        return "-"
    get_movimiento_caja_display.short_description = "Movimiento Caja"

    def cantidad_neta_display(self, obj):
        """Display method for cantidad_neta to avoid recursion issues"""
        return obj.cantidad_neta()
    cantidad_neta_display.short_description = "Cantidad Neta"

    def importe_neto_display(self, obj):
        """Display method for importe_neto to avoid recursion issues"""
        return f"{obj.importe_neto():.2f}€"
    importe_neto_display.short_description = "Importe Neto"

    def save_model(self, request, obj, form, change):
        obj.save(user=request.user)
        
        
@admin.register(Caja)
class CajaAdmin(admin.ModelAdmin):
    list_display = ('campamento', 'nombre', 'saldo_caja_display', 'saldo_desglose_display', 'activa', 'creado_por', 'creado_en')
    list_filter = ('activa', 'campamento')
    search_fields = ('nombre', 'campamento__nombre')
    ordering = ('-nombre',)
    readonly_fields = ('saldo_caja_display', 'saldo_desglose_display', 'creado_por', 'creado_en', 'modificado_por', 'modificado_en')  # Los saldos no se pueden modificar manualmente

    fieldsets = (
        ('Información Básica', {
            'fields': ('campamento', 'nombre', 'activa')
        }),
        ('Observaciones', {
            'fields': ('observaciones',),
            'classes': ('collapse',)
        }),
        ('Información de Creación y Modificación', {
            'fields': ('creado_por', 'creado_en', 'modificado_por', 'modificado_en'),
            'classes': ('collapse',)
        }),
    )
    
    def total_movimientos_caja(self, obj):
        return obj.movimientos.count()
    total_movimientos_caja.short_description = 'Mov. Caja'
    
    def total_turnos_ejercicio(self, obj):
        return obj.ejercicio.turnos.count()
    total_turnos_ejercicio.short_description = 'Turnos (Ejercicio)'
    
    def saldo_caja_display(self, obj):
        return f"{obj.calcular_saldo_caja():.2f}€"

    def saldo_desglose_display(self, obj):
        saldo_calc = obj.calcular_saldo_desde_desglose()
        if saldo_calc != obj.calcular_saldo_caja():
            return f"{saldo_calc:.2f}€ ⚠️"
        return f"{saldo_calc:.2f}€ ✓"
    saldo_desglose_display.short_description = 'Saldo desde desglose'

    def save_model(self, request, obj, form, change):
        obj.save(user=request.user)
