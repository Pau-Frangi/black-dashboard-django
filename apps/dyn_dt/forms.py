from django import forms
from .models import Concepto, Turno, Caja, MovimientoCaja, MovimientoBanco, DenominacionEuro, MovimientoDinero
from datetime import date, datetime
from apps.dyn_dt.models import Ejercicio
import os


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
        fields = ['ejercicio', 'nombre']
        widgets = {
            'ejercicio': forms.Select(attrs={
                'class': 'form-select'
            }),
            'nombre': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre del turno (ej. Primer turno chicas)'
            })
        }
        labels = {
            'ejercicio': 'Ejercicio',
            'nombre': 'Nombre del turno'
        }


class CajaForm(forms.ModelForm):
    """Form for creating and editing Caja instances."""
    
    class Meta:
        model = Caja
        fields = ['ejercicio', 'nombre', 'año', 'activa', 'saldo_caja', 'observaciones']
        widgets = {
            'ejercicio': forms.Select(attrs={
                'class': 'form-select'
            }),
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
            'saldo_caja': forms.NumberInput(attrs={
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
            'ejercicio': 'Ejercicio',
            'nombre': 'Nombre de la caja',
            'año': 'Año',
            'activa': '¿Caja activa?',
            'saldo_caja': 'Saldo inicial (€)',
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
    
    def save(self, commit=True):
        """Sobrescribir save para asegurar que la caja nueva tenga desglose inicializado"""
        caja = super().save(commit=commit)
        
        if commit and not caja.pk:  # Solo para cajas nuevas
            # La señal post_save se encargará de inicializar el desglose
            pass
            
        return caja


class MovimientoCajaForm(forms.ModelForm):
    """Form for creating and editing MovimientoCaja instances."""
    
    fecha_date = forms.DateField(
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        }),
        label='Fecha'
    )
    
    fecha_time = forms.TimeField(
        widget=forms.TimeInput(attrs={
            'class': 'form-control',
            'type': 'time'
        }),
        label='Hora'
    )
    
    class Meta:
        model = MovimientoCaja
        fields = ['caja', 'turno', 'concepto', 'cantidad', 'justificante', 'archivo_justificante', 'descripcion']
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
            'justificante': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nº de justificante (opcional)',
                'maxlength': 5
            }),
            'archivo_justificante': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf,.jpg,.jpeg,.png,.gif,.bmp'
            }),
            'descripcion': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Descripción detallada del movimiento'
            })
        }
        labels = {
            'caja': 'Caja',
            'turno': 'Turno',
            'concepto': 'Concepto',
            'cantidad': 'Cantidad (€)',
            'justificante': 'Nº Justificante',
            'archivo_justificante': 'Archivo Justificante',
            'descripcion': 'Descripción'
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Filter only active cajas
        self.fields['caja'].queryset = Caja.objects.filter(activa=True)
        
        # Filter turnos based on selected caja's ejercicio
        if 'caja' in self.data:
            try:
                caja_id = int(self.data.get('caja'))
                caja = Caja.objects.get(id=caja_id)
                self.fields['turno'].queryset = Turno.objects.filter(ejercicio=caja.ejercicio)
            except (ValueError, TypeError, Caja.DoesNotExist):
                self.fields['turno'].queryset = Turno.objects.none()
        elif self.instance.pk and self.instance.caja:
            self.fields['turno'].queryset = Turno.objects.filter(ejercicio=self.instance.caja.ejercicio)
        else:
            self.fields['turno'].queryset = Turno.objects.none()
        
        # Set default values
        if not self.instance.pk:
            from datetime import datetime
            now = datetime.now()
            self.fields['fecha_date'].initial = now.date()
            self.fields['fecha_time'].initial = now.time()
        else:
            self.fields['fecha_date'].initial = self.instance.fecha.date()
            self.fields['fecha_time'].initial = self.instance.fecha.time()

    def clean_archivo_justificante(self):
        """Validate uploaded file"""
        archivo = self.cleaned_data.get('archivo_justificante')
        
        if archivo:
            ext = os.path.splitext(archivo.name)[1].lower()
            valid_extensions = ['.pdf', '.jpg', '.jpeg', '.png', '.gif', '.bmp']
            
            if ext not in valid_extensions:
                raise forms.ValidationError(
                    f"El archivo debe ser una imagen (JPG, PNG, GIF, BMP) o un PDF. "
                    f"Extensión recibida: {ext}"
                )
            
            # Limitar tamaño de archivo a 10MB
            if archivo.size > 10 * 1024 * 1024:
                raise forms.ValidationError("El archivo no puede superar los 10MB")
        
        return archivo

    def clean(self):
        """Validación adicional para campos de justificante"""
        cleaned_data = super().clean()
        concepto = cleaned_data.get('concepto')
        justificante = cleaned_data.get('justificante')
        archivo_justificante = cleaned_data.get('archivo_justificante')
        
        # Si el concepto es un gasto, limpiar campos de justificante si no son gastos
        if concepto and not concepto.es_gasto:
            # Para ingresos, limpiar campos de justificante
            cleaned_data['justificante'] = None
            cleaned_data['archivo_justificante'] = None
        
        return cleaned_data


class MovimientoBancoForm(forms.ModelForm):
    """Form for creating and editing MovimientoBanco instances."""
    
    fecha_date = forms.DateField(
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        }),
        label='Fecha'
    )
    
    fecha_time = forms.TimeField(
        widget=forms.TimeInput(attrs={
            'class': 'form-control',
            'type': 'time'
        }),
        label='Hora'
    )
    
    class Meta:
        model = MovimientoBanco
        fields = ['ejercicio', 'turno', 'concepto', 'cantidad', 'referencia_bancaria', 'archivo_justificante', 'descripcion']
        widgets = {
            'ejercicio': forms.Select(attrs={
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
            'referencia_bancaria': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Referencia bancaria (opcional)',
                'maxlength': 50
            }),
            'archivo_justificante': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf,.jpg,.jpeg,.png,.gif,.bmp'
            }),
            'descripcion': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Descripción detallada del movimiento bancario'
            })
        }
        labels = {
            'ejercicio': 'Ejercicio',
            'turno': 'Turno',
            'concepto': 'Concepto',
            'cantidad': 'Cantidad (€)',
            'referencia_bancaria': 'Referencia Bancaria',
            'archivo_justificante': 'Archivo Justificante',
            'descripcion': 'Descripción'
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Filter turnos based on selected ejercicio
        if 'ejercicio' in self.data:
            try:
                ejercicio_id = int(self.data.get('ejercicio'))
                self.fields['turno'].queryset = Turno.objects.filter(ejercicio_id=ejercicio_id)
            except (ValueError, TypeError):
                self.fields['turno'].queryset = Turno.objects.none()
        elif self.instance.pk and self.instance.ejercicio:
            self.fields['turno'].queryset = Turno.objects.filter(ejercicio=self.instance.ejercicio)
        else:
            self.fields['turno'].queryset = Turno.objects.none()

    def clean(self):
        """Additional validation for bank movements"""
        cleaned_data = super().clean()
        # If no turno is selected, create a default "General" turno for this ejercicio
        if not cleaned_data.get('turno') and cleaned_data.get('ejercicio'):
            turno, created = Turno.objects.get_or_create(
                ejercicio=cleaned_data['ejercicio'],
                nombre="General",
                defaults={
                    'creado_por': self.instance.creado_por if self.instance.pk else None
                }
            )
            cleaned_data['turno'] = turno
        return cleaned_data


class MovimientoDineroForm(forms.ModelForm):
    """Form for creating and editing MovimientoDinero instances."""
    
    class Meta:
        model = MovimientoDinero
        fields = ['denominacion', 'cantidad_entrada', 'cantidad_salida']
        widgets = {
            'denominacion': forms.HiddenInput(),
            'cantidad_entrada': forms.NumberInput(attrs={
                'class': 'form-control form-control-sm',
                'min': '0',
                'placeholder': '0'
            }),
            'cantidad_salida': forms.NumberInput(attrs={
                'class': 'form-control form-control-sm',
                'min': '0',
                'placeholder': '0'
            })
        }


# Formset para manejar múltiples MovimientoDinero
MovimientoDineroFormSet = forms.modelformset_factory(
    MovimientoDinero,
    form=MovimientoDineroForm,
    extra=0,  # No crear formularios extra por defecto
    can_delete=False
)


class DesgloseDineroForm(forms.Form):
    """
    Formulario dinámico para el desglose de dinero en movimientos.
    Se genera basándose en las denominaciones activas.
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Obtener todas las denominaciones activas
        denominaciones = DenominacionEuro.objects.filter(activa=True).order_by('-valor')
        
        for denominacion in denominaciones:
            # Campo para cantidad que entra
            self.fields[f'entrada_{denominacion.id}'] = forms.IntegerField(
                required=False,
                min_value=0,
                initial=0,
                widget=forms.NumberInput(attrs={
                    'class': 'form-control form-control-sm',
                    'placeholder': '0',
                    'data-denominacion': denominacion.id,
                    'data-valor': float(denominacion.valor),
                    'data-tipo': 'entrada'
                }),
                label=f'Entra {denominacion.valor}€'
            )
            
            # Campo para cantidad que sale
            self.fields[f'salida_{denominacion.id}'] = forms.IntegerField(
                required=False,
                min_value=0,
                initial=0,
                widget=forms.NumberInput(attrs={
                    'class': 'form-control form-control-sm',
                    'placeholder': '0',
                    'data-denominacion': denominacion.id,
                    'data-valor': float(denominacion.valor),
                    'data-tipo': 'salida'
                }),
                label=f'Sale {denominacion.valor}€'
            )
    
    def get_movimientos_dinero_data(self):
        """
        Procesa los datos del formulario y retorna una lista de datos
        para crear objetos MovimientoDinero
        """
        if not self.is_valid():
            return []
        
        movimientos_data = []
        denominaciones = DenominacionEuro.objects.filter(activa=True)
        
        for denominacion in denominaciones:
            entrada = self.cleaned_data.get(f'entrada_{denominacion.id}', 0) or 0
            salida = self.cleaned_data.get(f'salida_{denominacion.id}', 0) or 0
            
            # Solo crear el movimiento si hay entrada o salida
            if entrada > 0 or salida > 0:
                movimientos_data.append({
                    'denominacion': denominacion,
                    'cantidad_entrada': entrada,
                    'cantidad_salida': salida
                })
        
        return movimientos_data


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
    
    ejercicio = forms.ModelChoiceField(
        queryset=Ejercicio.objects.all(),
        required=False,
        empty_label="Todos los ejercicios",
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
                "La fecha 'desde' no puede ser posterior a la fecha 'hasta'."
            )

        if solo_gastos and solo_ingresos:
            raise forms.ValidationError(
                "No se pueden seleccionar 'Solo gastos' y 'Solo ingresos' al mismo tiempo."
            )

        return cleaned_data

