from django import forms
from .models import Concepto, Turno, Caja, MovimientoCaja
from datetime import date


class ConceptoForm(forms.ModelForm):
    """Form for creating and editing Concepto instances."""
    
    class Meta:
        model = Concepto
        fields = ['nombre', 'es_gasto']
        widgets = {
            'nombre': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre del concepto (ej. Alimentos, Inscripciones)'
            }),
            'es_gasto': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            })
        }
        labels = {
            'nombre': 'Nombre del concepto',
            'es_gasto': '¿Es un gasto?'
        }


class TurnoForm(forms.ModelForm):
    """Form for creating and editing Turno instances."""
    
    class Meta:
        model = Turno
        fields = ['nombre']
        widgets = {
            'nombre': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre del turno (ej. Primer turno chicas)'
            })
        }
        labels = {
            'nombre': 'Nombre del turno'
        }


class CajaForm(forms.ModelForm):
    """Form for creating and editing Caja instances."""
    
    class Meta:
        model = Caja
        fields = ['nombre', 'año', 'activa', 'saldo', 'observaciones']
        widgets = {
            'nombre': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre de la caja (ej. Caja 2025)'
            }),
            'año': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 2020,
                'max': 2030,
                'value': date.today().year
            }),
            'activa': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'saldo': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0'
            }),
            'observaciones': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Observaciones adicionales (opcional)'
            })
        }
        labels = {
            'nombre': 'Nombre de la caja',
            'año': 'Año',
            'activa': '¿Caja activa?',
            'saldo': 'Saldo inicial (€)',
            'observaciones': 'Observaciones'
        }

    def clean_año(self):
        """Validate that the year is reasonable."""
        año = self.cleaned_data.get('año')
        current_year = date.today().year
        
        if año < 2020 or año > current_year + 5:
            raise forms.ValidationError(
                f"El año debe estar entre 2020 y {current_year + 5}"
            )
        
        return año


class MovimientoCajaForm(forms.ModelForm):
    """Form for creating and editing MovimientoCaja instances."""
    
    class Meta:
        model = MovimientoCaja
        fields = ['caja', 'turno', 'concepto', 'cantidad', 'fecha', 'justificante', 'observaciones']
        widgets = {
            'caja': forms.Select(attrs={
                'class': 'form-select'
            }),
            'turno': forms.Select(attrs={
                'class': 'form-select'
            }),
            'concepto': forms.Select(attrs={
                'class': 'form-select'
            }),
            'cantidad': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0.01',
                'placeholder': '0.00'
            }),
            'fecha': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'justificante': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nº de justificante (opcional)',
                'maxlength': 5
            }),
            'observaciones': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Observaciones adicionales (opcional)'
            })
        }
        labels = {
            'caja': 'Caja',
            'turno': 'Turno',
            'concepto': 'Concepto',
            'cantidad': 'Cantidad (€)',
            'fecha': 'Fecha del movimiento',
            'justificante': 'Nº Justificante',
            'observaciones': 'Observaciones'
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Filter only active cajas
        self.fields['caja'].queryset = Caja.objects.filter(activa=True)
        
        # Set default date to today
        if not self.instance.pk:
            self.fields['fecha'].initial = date.today()

    def clean_cantidad(self):
        """Validate that cantidad is positive."""
        cantidad = self.cleaned_data.get('cantidad')
        
        if cantidad <= 0:
            raise forms.ValidationError("La cantidad debe ser mayor que 0")
        
        return cantidad

    def clean(self):
        """Additional form validation."""
        cleaned_data = super().clean()
        caja = cleaned_data.get('caja')
        
        if caja and not caja.activa:
            raise forms.ValidationError(
                "No se pueden añadir movimientos a una caja inactiva"
            )
        
        return cleaned_data


class MovimientoCajaFilterForm(forms.Form):
    """Form for filtering MovimientoCaja instances."""
    
    caja = forms.ModelChoiceField(
        queryset=Caja.objects.all(),
        required=False,
        empty_label="Todas las cajas",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    turno = forms.ModelChoiceField(
        queryset=Turno.objects.all(),
        required=False,
        empty_label="Todos los turnos",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    concepto = forms.ModelChoiceField(
        queryset=Concepto.objects.all(),
        required=False,
        empty_label="Todos los conceptos",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    fecha_desde = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        }),
        label="Fecha desde"
    )
    
    fecha_hasta = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        }),
        label="Fecha hasta"
    )
    
    solo_gastos = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        label="Solo gastos"
    )
    
    solo_ingresos = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        label="Solo ingresos"
    )

    def clean(self):
        """Validate that fecha_desde is not after fecha_hasta."""
        cleaned_data = super().clean()
        fecha_desde = cleaned_data.get('fecha_desde')
        fecha_hasta = cleaned_data.get('fecha_hasta')
        solo_gastos = cleaned_data.get('solo_gastos')
        solo_ingresos = cleaned_data.get('solo_ingresos')
        
        if fecha_desde and fecha_hasta and fecha_desde > fecha_hasta:
            raise forms.ValidationError(
                "La fecha 'desde' no puede ser posterior a la fecha 'hasta'"
            )
        
        if solo_gastos and solo_ingresos:
            raise forms.ValidationError(
                "No se pueden seleccionar 'Solo gastos' y 'Solo ingresos' al mismo tiempo"
            )
        
        return cleaned_data
