from django import forms
from .models import *

# Clase base para aplicar estilos Bootstrap
class BaseMovimientoCajaForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-control'})


class MovimientoCajaIngresoForm(BaseMovimientoCajaForm):
    class Meta:
        model = MovimientoCajaIngreso
        fields = [
            'ejercicio', 'caja', 'importe', 'turno', 'fecha', 'descripcion',
            'concepto', 'archivo'
        ]


class MovimientoCajaGastoForm(BaseMovimientoCajaForm):
    class Meta:
        model = MovimientoCajaGasto
        fields = [
            'ejercicio', 'caja', 'importe', 'turno', 'fecha', 'descripcion',
            'concepto', 'archivo'
        ]


class MovimientoCajaTransferenciaForm(BaseMovimientoCajaForm):
    class Meta:
        model = MovimientoCajaTransferencia
        fields = [
            'ejercicio', 'caja', 'importe', 'turno', 'fecha', 'descripcion',
            'caja_destino'
        ]


class MovimientoCajaDepositoForm(BaseMovimientoCajaForm):
    class Meta:
        model = MovimientoCajaDeposito
        fields = [
            'ejercicio', 'caja', 'importe', 'turno', 'fecha', 'descripcion'
        ]


class MovimientoCajaRetiradaForm(BaseMovimientoCajaForm):
    class Meta:
        model = MovimientoCajaRetirada
        fields = [
            'ejercicio', 'caja', 'importe', 'turno', 'fecha', 'descripcion',
            'retirado_por'
        ]
