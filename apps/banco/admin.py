from django.contrib import admin
from .models import *
from django.utils.html import format_html


@admin.register(ViaMovimientoBanco)
class ViaMovimientoBancoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'creado_por', 'creado_en')
    list_filter = ('nombre',)
    ordering = ('-creado_en',)
    readonly_fields = ('creado_por', 'creado_en', 'modificado_por', 'modificado_en')

    def save_model(self, request, obj, form, change):
        obj.save(user=request.user)


@admin.register(CuentaBancaria)
class CuentaBancariaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'IBAN', 'titular', 'activo', 'creado_por', 'creado_en')
    list_filter = ('activo',)
    search_fields = ('nombre', 'IBAN')
    ordering = ('-creado_en',)
    readonly_fields = ('creado_por', 'creado_en', 'modificado_por', 'modificado_en')

    def save_model(self, request, obj, form, change):
        obj.save(user=request.user)
        
        
@admin.register(MovimientoBancoIngreso)
class MovimientoBancoIngresoAdmin(admin.ModelAdmin):
    list_display = ('fecha_display', 'ejercicio', 'campamento', 'cuenta_bancaria', 'via', 'turno', 'concepto', 'importe_display', 'descripcion', 'archivo_display', 'creado_por', 'creado_en')
    search_fields = ('cuenta_bancaria__nombre', 'concepto__nombre')
    list_filter = ('fecha', 'cuenta_bancaria', 'turno', 'ejercicio', 'creado_por', 'creado_en', 'concepto', 'campamento')
    ordering = ('-fecha',)
    readonly_fields = ('creado_por', 'creado_en', 'modificado_por', 'modificado_en')


    fieldsets = (
        ('Información básica', {
            'fields': ('fecha', 'ejercicio', 'campamento', 'cuenta_bancaria', 'via', 'turno', 'concepto', 'importe')
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
        
        
        
@admin.register(MovimientoBancoGasto)
class MovimientoBancoGastoAdmin(admin.ModelAdmin):
    list_display = ('fecha_display', 'ejercicio', 'campamento', 'turno', 'concepto', 'importe_display', 'descripcion', 'archivo_display', 'creado_por', 'creado_en')
    search_fields = ('concepto__nombre',)
    list_filter = ('fecha', 'turno', 'ejercicio', 'creado_por', 'creado_en', 'concepto', 'campamento')
    ordering = ('-fecha',)
    readonly_fields = ('creado_por', 'creado_en', 'modificado_por', 'modificado_en')

    fieldsets = (
        ('Información básica', {
            'fields': ('fecha', 'ejercicio', 'campamento', 'turno', 'concepto', 'importe')
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