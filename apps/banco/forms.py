from django import forms
from .models import *
from apps.dyn_dt.models import Turno, Concepto, Ejercicio, Campamento


class UserTrackedModelForm(forms.ModelForm):
    """
    Base form class that automatically handles creado_por and modificado_por fields
    """
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        
        if self.user:
            if not instance.pk:  # New instance
                instance.creado_por = self.user
            instance.modificado_por = self.user
        
        if commit:
            instance.save()
        return instance


class CuentaBancariaForm(UserTrackedModelForm):
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


class ViaMovimientoBancoForm(UserTrackedModelForm):
    class Meta:
        model = ViaMovimientoBanco
        fields = ['nombre']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: Bizum, Transferencia, etc.'}),
        }


class MovimientoBancoIngresoForm(UserTrackedModelForm):
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
        model = MovimientoBancoIngreso
        fields = ['ejercicio', 'campamento', 'cuenta_bancaria', 'via', 'turno', 'concepto', 'importe', 'descripcion', 'referencia_bancaria', 'archivo']
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
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filter conceptos to show only those that are not gastos
        self.fields['concepto'].queryset = Concepto.objects.filter(es_gasto=False)
        # Filter cuenta_bancaria to show only active ones
        self.fields['cuenta_bancaria'].queryset = CuentaBancaria.objects.filter(activo=True)

    def save(self, commit=True):
        instance = super().save(commit=False)
        # Combine fecha and hora into datetime
        from datetime import datetime, time
        fecha = self.cleaned_data['fecha']
        hora = self.cleaned_data['hora']
        instance.fecha = datetime.combine(fecha, hora)
        
        # Call parent save to handle user tracking
        if commit:
            # Handle user tracking from parent class
            if self.user:
                if not instance.pk:  # New instance
                    instance.creado_por = self.user
                instance.modificado_por = self.user
            instance.save()
        return instance


class MovimientoBancoGastoForm(UserTrackedModelForm):
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
        model = MovimientoBancoGasto
        fields = ['ejercicio', 'campamento', 'cuenta_bancaria', 'turno', 'concepto', 'importe', 'descripcion', 'referencia_bancaria', 'archivo']
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
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filter conceptos to show only those that are gastos
        self.fields['concepto'].queryset = Concepto.objects.filter(es_gasto=True)
        # Filter cuenta_bancaria to show only active ones
        self.fields['cuenta_bancaria'].queryset = CuentaBancaria.objects.filter(activo=True)

    def save(self, commit=True):
        instance = super().save(commit=False)
        # Combine fecha and hora into datetime
        from datetime import datetime, time
        fecha = self.cleaned_data['fecha']
        hora = self.cleaned_data['hora']
        instance.fecha = datetime.combine(fecha, hora)
        
        # Call parent save to handle user tracking
        if commit:
            # Handle user tracking from parent class
            if self.user:
                if not instance.pk:  # New instance
                    instance.creado_por = self.user
                instance.modificado_por = self.user
            instance.save()
        return instance


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
