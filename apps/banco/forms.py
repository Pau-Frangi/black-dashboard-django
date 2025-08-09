from django import forms
from .models import *
from apps.dyn_dt.models import Turno, Concepto, Ejercicio, Campamento


class CuentaBancariaForm(forms.ModelForm):
    class Meta:
        model = CuentaBancaria
        fields = ['nombre', 'titular', 'IBAN', 'activo']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre de la cuenta'}),
            'titular': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Titular de la cuenta'}),
            'IBAN': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'ES00 0000 0000 0000 0000 0000'}),
            'activo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def clean_IBAN(self):
        iban = self.cleaned_data.get('IBAN')
        if iban:
            # Remove spaces and convert to uppercase
            iban = iban.replace(' ', '').upper()
            # Basic IBAN validation (Spanish IBAN should be 24 characters)
            if not iban.startswith('ES') or len(iban) != 24:
                raise forms.ValidationError("El IBAN debe ser válido y comenzar con ES (24 caracteres)")
        return iban


class ViaMovimientoBancoForm(forms.ModelForm):
    class Meta:
        model = ViaMovimientoBanco
        fields = ['nombre']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: Bizum, Transferencia, etc.'}),
        }


class MovimientoBancoIngresoForm(forms.ModelForm):
    class Meta:
        model = MovimientoBancoIngreso
        fields = ['ejercicio', 'campamento', 'cuenta_bancaria', 'via', 'turno', 'concepto', 'importe', 'descripcion', 'referencia_bancaria', 'archivo', 'fecha']
        widgets = {
            'ejercicio': forms.Select(attrs={'class': 'form-control'}),
            'campamento': forms.Select(attrs={'class': 'form-control'}),
            'cuenta_bancaria': forms.Select(attrs={'class': 'form-control'}),
            'via': forms.Select(attrs={'class': 'form-control'}),
            'turno': forms.Select(attrs={'class': 'form-control'}),
            'concepto': forms.Select(attrs={'class': 'form-control'}),
            'importe': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0.01'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'referencia_bancaria': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Referencia bancaria (opcional)'}),
            'archivo': forms.FileInput(attrs={'class': 'form-control'}),
            'fecha': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filter conceptos to show only those that are not gastos
        self.fields['concepto'].queryset = Concepto.objects.filter(es_gasto=False)
        # Filter cuenta_bancaria to show only active ones
        self.fields['cuenta_bancaria'].queryset = CuentaBancaria.objects.filter(activo=True)


class MovimientoBancoGastoForm(forms.ModelForm):
    class Meta:
        model = MovimientoBancoGasto
        fields = ['ejercicio', 'campamento', 'cuenta_bancaria', 'turno', 'concepto', 'importe', 'descripcion', 'referencia_bancaria', 'archivo', 'fecha']
        widgets = {
            'ejercicio': forms.Select(attrs={'class': 'form-control'}),
            'campamento': forms.Select(attrs={'class': 'form-control'}),
            'cuenta_bancaria': forms.Select(attrs={'class': 'form-control'}),
            'turno': forms.Select(attrs={'class': 'form-control'}),
            'concepto': forms.Select(attrs={'class': 'form-control'}),
            'importe': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0.01'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'referencia_bancaria': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Referencia bancaria (opcional)'}),
            'archivo': forms.FileInput(attrs={'class': 'form-control'}),
            'fecha': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filter conceptos to show only those that are gastos
        self.fields['concepto'].queryset = Concepto.objects.filter(es_gasto=True)
        # Filter cuenta_bancaria to show only active ones
        self.fields['cuenta_bancaria'].queryset = CuentaBancaria.objects.filter(activo=True)


# Filter forms for admin or list views
class CuentaBancariaFilterForm(forms.Form):
    activo = forms.ChoiceField(
        choices=[('', 'Todas'), (True, 'Activas'), (False, 'Inactivas')],
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    titular = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Buscar por titular'})
    )


class MovimientoBancoFilterForm(forms.Form):
    ejercicio = forms.ModelChoiceField(
        queryset=Ejercicio.objects.all(),
        required=False,
        empty_label="Todos los ejercicios",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    campamento = forms.ModelChoiceField(
        queryset=Campamento.objects.all(),
        required=False,
        empty_label="Todos los campamentos",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    cuenta_bancaria = forms.ModelChoiceField(
        queryset=CuentaBancaria.objects.filter(activo=True),
        required=False,
        empty_label="Todas las cuentas",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    via = forms.ModelChoiceField(
        queryset=ViaMovimientoBanco.objects.all(),
        required=False,
        empty_label="Todas las vías",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    turno = forms.ModelChoiceField(
        queryset=Turno.objects.all(),
        required=False,
        empty_label="Todos los turnos",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    concepto = forms.ModelChoiceField(
        queryset=Concepto.objects.all(),
        required=False,
        empty_label="Todos los conceptos",
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
    importe_minimo = forms.DecimalField(
        required=False,
        max_digits=10,
        decimal_places=2,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': 'Importe mínimo'})
    )
    importe_maximo = forms.DecimalField(
        required=False,
        max_digits=10,
        decimal_places=2,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': 'Importe máximo'})
    )


class ViaMovimientoBancoFilterForm(forms.Form):
    nombre = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Buscar por nombre'})
    )


# Bulk action forms
class BulkMovimientoBancoForm(forms.Form):
    """Form for bulk operations on bank movements"""
    ejercicio = forms.ModelChoiceField(
        queryset=Ejercicio.objects.all(),
        required=False,
        empty_label="Sin cambios",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    campamento = forms.ModelChoiceField(
        queryset=Campamento.objects.all(),
        required=False,
        empty_label="Sin cambios",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    cuenta_bancaria = forms.ModelChoiceField(
        queryset=CuentaBancaria.objects.filter(activo=True),
        required=False,
        empty_label="Sin cambios",
        widget=forms.Select(attrs={'class': 'form-control'})
    )


# Quick entry forms (simplified versions)
class QuickMovimientoBancoIngresoForm(forms.ModelForm):
    """Simplified form for quick bank income entry"""
    class Meta:
        model = MovimientoBancoIngreso
        fields = ['cuenta_bancaria', 'via', 'concepto', 'importe', 'descripcion']
        widgets = {
            'cuenta_bancaria': forms.Select(attrs={'class': 'form-control'}),
            'via': forms.Select(attrs={'class': 'form-control'}),
            'concepto': forms.Select(attrs={'class': 'form-control'}),
            'importe': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0.01'}),
            'descripcion': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Descripción breve'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['concepto'].queryset = Concepto.objects.filter(es_gasto=False)
        self.fields['cuenta_bancaria'].queryset = CuentaBancaria.objects.filter(activo=True)


class QuickMovimientoBancoGastoForm(forms.ModelForm):
    """Simplified form for quick bank expense entry"""
    class Meta:
        model = MovimientoBancoGasto
        fields = ['cuenta_bancaria', 'concepto', 'importe', 'descripcion']
        widgets = {
            'cuenta_bancaria': forms.Select(attrs={'class': 'form-control'}),
            'concepto': forms.Select(attrs={'class': 'form-control'}),
            'importe': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0.01'}),
            'descripcion': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Descripción breve'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['concepto'].queryset = Concepto.objects.filter(es_gasto=True)
        self.fields['cuenta_bancaria'].queryset = CuentaBancaria.objects.filter(activo=True)
