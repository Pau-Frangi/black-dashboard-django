from django import forms
from .models import *
from apps.dyn_dt.models import Turno, Concepto, Ejercicio, Campamento


class CajaForm(forms.ModelForm):
    class Meta:
        model = Caja
        fields = ['campamento', 'nombre', 'activa', 'observaciones']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre de la caja'}),
            'observaciones': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'campamento': forms.Select(attrs={'class': 'form-control'}),
            'activa': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class DenominacionEuroForm(forms.ModelForm):
    class Meta:
        model = DenominacionEuro
        fields = ['valor', 'es_billete', 'activa']
        widgets = {
            'valor': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'es_billete': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'activa': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class MovimientoCajaIngresoForm(forms.ModelForm):
    # Add custom field for combined date and time handling
    fecha = forms.DateField(
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        required=True
    )
    hora = forms.TimeField(
        widget=forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
        required=True
    )

    class Meta:
        model = MovimientoCajaIngreso
        fields = ['ejercicio', 'caja', 'turno', 'concepto', 'importe', 'descripcion', 'archivo']
        widgets = {
            'ejercicio': forms.Select(attrs={'class': 'form-control'}),
            'caja': forms.Select(attrs={'class': 'form-control'}),
            'turno': forms.Select(attrs={'class': 'form-control'}),
            'concepto': forms.Select(attrs={'class': 'form-control'}),
            'importe': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0.01'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'archivo': forms.FileInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filter conceptos to show only those that are not gastos
        self.fields['concepto'].queryset = Concepto.objects.filter(es_gasto=False)

    def save(self, commit=True):
        instance = super().save(commit=False)
        # Combine fecha and hora into datetime
        from datetime import datetime, time
        fecha = self.cleaned_data['fecha']
        hora = self.cleaned_data['hora']
        instance.fecha = datetime.combine(fecha, hora)
        
        if commit:
            instance.save()
        return instance


class MovimientoCajaGastoForm(forms.ModelForm):
    # Add custom field for combined date and time handling + justificante
    fecha = forms.DateField(
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        required=True
    )
    hora = forms.TimeField(
        widget=forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
        required=True
    )
    justificante = forms.CharField(
        max_length=5,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '12345', 'maxlength': '5'})
    )

    class Meta:
        model = MovimientoCajaGasto
        fields = ['ejercicio', 'caja', 'turno', 'concepto', 'importe', 'descripcion', 'archivo']
        widgets = {
            'ejercicio': forms.Select(attrs={'class': 'form-control'}),
            'caja': forms.Select(attrs={'class': 'form-control'}),
            'turno': forms.Select(attrs={'class': 'form-control'}),
            'concepto': forms.Select(attrs={'class': 'form-control'}),
            'importe': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0.01'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'archivo': forms.FileInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filter conceptos to show only those that are gastos
        self.fields['concepto'].queryset = Concepto.objects.filter(es_gasto=True)

    def save(self, commit=True):
        instance = super().save(commit=False)
        # Combine fecha and hora into datetime
        from datetime import datetime, time
        fecha = self.cleaned_data['fecha']
        hora = self.cleaned_data['hora']
        instance.fecha = datetime.combine(fecha, hora)
        
        if commit:
            instance.save()
        return instance


class MovimientoCajaTransferenciaForm(forms.ModelForm):
    class Meta:
        model = MovimientoCajaTransferencia
        fields = ['ejercicio', 'caja_origen', 'caja_destino', 'turno', 'importe', 'descripcion', 'fecha']
        widgets = {
            'ejercicio': forms.Select(attrs={'class': 'form-control'}),
            'caja_origen': forms.Select(attrs={'class': 'form-control'}),
            'caja_destino': forms.Select(attrs={'class': 'form-control'}),
            'turno': forms.Select(attrs={'class': 'form-control'}),
            'importe': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0.01'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'fecha': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        caja_origen = cleaned_data.get('caja_origen')
        caja_destino = cleaned_data.get('caja_destino')

        if caja_origen and caja_destino and caja_origen == caja_destino:
            raise forms.ValidationError("La caja de origen y destino no pueden ser la misma.")

        return cleaned_data


class MovimientoCajaDepositoForm(forms.ModelForm):
    class Meta:
        model = MovimientoCajaDeposito
        fields = ['ejercicio', 'caja', 'turno', 'importe', 'descripcion', 'fecha']
        widgets = {
            'ejercicio': forms.Select(attrs={'class': 'form-control'}),
            'caja': forms.Select(attrs={'class': 'form-control'}),
            'turno': forms.Select(attrs={'class': 'form-control'}),
            'importe': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0.01'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'fecha': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
        }


class MovimientoCajaRetiradaForm(forms.ModelForm):
    class Meta:
        model = MovimientoCajaRetirada
        fields = ['ejercicio', 'caja', 'turno', 'importe', 'descripcion', 'retirado_por', 'fecha']
        widgets = {
            'ejercicio': forms.Select(attrs={'class': 'form-control'}),
            'caja': forms.Select(attrs={'class': 'form-control'}),
            'turno': forms.Select(attrs={'class': 'form-control'}),
            'importe': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0.01'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'retirado_por': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre de quien retira'}),
            'fecha': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
        }


class DesgloseCajaForm(forms.ModelForm):
    class Meta:
        model = DesgloseCaja
        fields = ['caja', 'denominacion', 'cantidad']
        widgets = {
            'caja': forms.Select(attrs={'class': 'form-control'}),
            'denominacion': forms.Select(attrs={'class': 'form-control'}),
            'cantidad': forms.NumberInput(attrs={'class': 'form-control', 'min': '0'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filter denominaciones to show only active ones
        self.fields['denominacion'].queryset = DenominacionEuro.objects.filter(activa=True)


class MovimientoEfectivoForm(forms.ModelForm):
    class Meta:
        model = MovimientoEfectivo
        fields = ['caja', 'denominacion', 'cantidad_entrada', 'cantidad_salida']
        widgets = {
            'caja': forms.Select(attrs={'class': 'form-control'}),
            'denominacion': forms.Select(attrs={'class': 'form-control'}),
            'cantidad_entrada': forms.NumberInput(attrs={'class': 'form-control', 'min': '0'}),
            'cantidad_salida': forms.NumberInput(attrs={'class': 'form-control', 'min': '0'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filter denominaciones to show only active ones
        self.fields['denominacion'].queryset = DenominacionEuro.objects.filter(activa=True)


# Filter forms for admin or list views
class CajaFilterForm(forms.Form):
    campamento = forms.ModelChoiceField(
        queryset=Campamento.objects.all(),
        required=False,
        empty_label="Todos los campamentos",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    activa = forms.ChoiceField(
        choices=[('', 'Todas'), (True, 'Activas'), (False, 'Inactivas')],
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )


class MovimientoFilterForm(forms.Form):
    ejercicio = forms.ModelChoiceField(
        queryset=Ejercicio.objects.all(),
        required=False,
        empty_label="Todos los ejercicios",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    caja = forms.ModelChoiceField(
        queryset=Caja.objects.all(),
        required=False,
        empty_label="Todas las cajas",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    turno = forms.ModelChoiceField(
        queryset=Turno.objects.all(),
        required=False,
        empty_label="Todos los turnos",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    fecha_desde = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )
    fecha_hasta = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )
