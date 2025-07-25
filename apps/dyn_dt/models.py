from django.db import models
from decimal import Decimal
from django.utils.translation import gettext_lazy as _
from datetime import date
from django.core.exceptions import ValidationError
from django.db.models.signals import post_save, pre_delete, post_delete
from django.dispatch import receiver
from django.utils import timezone
import os
from .mixins import UserTrackingMixin

# Create your models here.

class PageItems(models.Model):
	parent = models.CharField(max_length=255, null=True, blank=True)
	items_per_page = models.IntegerField(default=25)
	
class HideShowFilter(models.Model):
	parent = models.CharField(max_length=255, null=True, blank=True)
	key = models.CharField(max_length=255)
	value = models.BooleanField(default=False)

	def __str__(self):
		return self.key

class ModelFilter(models.Model):
	parent = models.CharField(max_length=255, null=True, blank=True)
	key = models.CharField(max_length=255)
	value = models.CharField(max_length=255)

	def __str__(self):
		return self.key


class Ejercicio(UserTrackingMixin, models.Model):
    """
    Representa un ejercicio económico que agrupa varias cajas.
    Cada ejercicio tiene su propio saldo bancario y calcula el saldo total
    como la suma de todas las cajas más el saldo bancario del ejercicio.
    """
    nombre = models.CharField(
        max_length=100,
        unique=True,
        verbose_name="Nombre del ejercicio",
        help_text="Ej: 'Ejercicio 2025'"
    )

    año = models.PositiveIntegerField(
        verbose_name="Año",
        help_text="Año correspondiente a este ejercicio (ej. 2025)"
    )

    activo = models.BooleanField(
        default=True,
        verbose_name="¿Ejercicio activo?",
        help_text="Marca si este ejercicio está actualmente en uso"
    )

    saldo_banco = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        verbose_name="Saldo bancario del ejercicio",
        help_text="Saldo bancario propio del ejercicio, independiente de las cajas"
    )

    descripcion = models.TextField(
        blank=True,
        null=True,
        verbose_name="Descripción",
        help_text="Descripción adicional del ejercicio"
    )
    
    creado_por = models.ForeignKey(
        'auth.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Creado por",
        help_text="Usuario que creó este ejercicio"
    )

    creado_en = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Creado en",
        help_text="Fecha y hora de creación del ejercicio"
    )
    
    def calcular_resultado_caja_ejercicio(self, campamento=None):
        """
        Calcula la suma del importe de todos los movimientos de caja asociados a este ejercicio.
        """
        total = Decimal('0.00')
        for movimiento_caja in MovimientoCaja.objects.filter(ejercicio=self, caja__campamento=campamento):
            total += movimiento_caja.cantidad_real()
        return total

    def calcular_resultado_banco_ejercicio(self, campamento=None):
        """
        Calcula la suma del importe de todos los movimientos bancarios asociados a este ejercicio.
        """
        total = Decimal('0.00')
        for movimiento_banco in MovimientoBanco.objects.filter(ejercicio=self, campamento=campamento):
            total += movimiento_banco.cantidad_real()
        return total

    def calcular_resultado_ejercicio(self, campamento=None):
        """
        Calcula el resultado total del ejercicio como la suma de los resultados de caja y banco.
        """
        resultado_caja = self.calcular_resultado_caja_ejercicio(campamento=campamento)
        resultado_banco = self.calcular_resultado_banco_ejercicio(campamento=campamento)
        return resultado_caja + resultado_banco

    def calcular_saldo_cajas(self, campamento=None):
        """
        Calcula la suma de todos los resultados de caja de los ejercicios desde el primero año hasta el actual.
        """
        total = Decimal('0.00')
        for ejercicio in Ejercicio.objects.filter(año__lte=self.año):
            total += ejercicio.calcular_resultado_caja_ejercicio(campamento=campamento)
        return total

    def calcular_saldo_banco(self, campamento=None):
        """
        Calcula la suma de todos los resultados de banco de los ejercicios desde el primero año hasta el actual.
        """
        total = Decimal('0.00')
        for ejercicio in Ejercicio.objects.filter(año__lte=self.año):
            total += ejercicio.calcular_resultado_banco_ejercicio(campamento=campamento)
        return total

    def calcular_saldo_total(self, campamento=None):
        """
        Calcula el saldo total del banco para el ejercicio actual.
        """
        calcular_saldo_cajas = self.calcular_saldo_cajas(campamento=campamento)
        calcular_saldo_banco = self.calcular_saldo_banco(campamento=campamento)
        return calcular_saldo_cajas + calcular_saldo_banco

    @property
    def saldo_total(self):
        """
        Propiedad que retorna el saldo total calculado
        """
        return self.calcular_saldo_total()

    def recalcular_saldos_cajas(self):
        """
        Recalcula los saldos de todas las cajas asociadas
        """
        for caja in self.cajas.all():
            caja.recalcular_saldo()

    def __str__(self):
        return f"{self.nombre} ({self.año}) - Total: {self.saldo_total:.2f}€"

    class Meta:
        verbose_name = "Ejercicio"
        verbose_name_plural = "Ejercicios"
        ordering = ['-año']




class Turno(UserTrackingMixin, models.Model):
    """
    Representa un turno del campamento (por ejemplo: 'Primer turno chicas').
    Cada turno debe estar asociado a un ejercicio específico.
    """
    
    campamento = models.ForeignKey(
        'Campamento',
        on_delete=models.CASCADE,
        verbose_name="Campamento",
        related_name="turnos",
        help_text="Campamento al que pertenece este turno"
    )
    
    ejercicio = models.ForeignKey(
        'Ejercicio',
        on_delete=models.CASCADE,
        verbose_name="Ejercicio",
        related_name="turnos",
        help_text="Ejercicio al que pertenece este turno"
    )

    nombre = models.CharField(
        max_length=100,
        verbose_name="Nombre del turno"
    )
    
    creado_por = models.ForeignKey(
        'auth.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Creado por",
        help_text="Usuario que creó este ejercicio"
    )

    creado_en = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Creado en",
        help_text="Fecha y hora de creación del ejercicio"
    )

    def __str__(self):
        return f"{self.nombre} ({self.ejercicio.nombre}) - {self.campamento.nombre})"

    class Meta:
        verbose_name = "Turno"
        verbose_name_plural = "Turnos"
        ordering = ['ejercicio__nombre', 'nombre']
        unique_together = [['ejercicio', 'nombre']]  # Unique turno name per ejercicio



class Concepto(UserTrackingMixin, models.Model):
    """
    Representa un concepto económico, como 'Alimentos', 'Inscripciones', etc.
    Puede ser de tipo ingreso o gasto.
    """

    nombre = models.CharField(
        max_length=100,
        unique=True,
        verbose_name="Nombre del concepto"
    )

    es_gasto = models.BooleanField(
        default=False,
        verbose_name="¿Es gasto?",
        help_text="Marca si este concepto representa una salida de dinero"
    )
    
    creado_por = models.ForeignKey(
        'auth.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Creado por",
        help_text="Usuario que creó este ejercicio"
    )

    creado_en = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Creado en",
        help_text="Fecha y hora de creación del ejercicio"
    )

    def __str__(self):
        return self.nombre

    class Meta:
        verbose_name = "Concepto"
        verbose_name_plural = "Conceptos"
        ordering = ['nombre']

        

class Caja(UserTrackingMixin, models.Model):
    """
    Representa una caja general
    """
    
    campamento = models.ForeignKey(
        'Campamento',
        on_delete=models.CASCADE,
        verbose_name="Campamento",
        related_name="cajas",
        help_text="Campamento al que pertenece esta caja"
    )

    nombre = models.CharField(
        max_length=100,
        unique=True,
        verbose_name="Nombre de la caja",
        help_text="Ej: 'Caja 1"
    )

    activa = models.BooleanField(
        default=True,
        verbose_name="¿Caja activa?",
        help_text="Marca si esta caja está actualmente en uso"
    )

    saldo_caja = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name="Saldo de caja",
        help_text="Saldo de la caja. Se actualiza automáticamente."
    )

    observaciones = models.TextField(
        blank=True,
        null=True,
        verbose_name="Observaciones"
    )
    
    creado_por = models.ForeignKey(
        'auth.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Creado por",
        help_text="Usuario que creó esta caja"
    )

    creado_en = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Creado en",
        help_text="Fecha y hora de creación de la caja"
    )

    def clean(self):
        """Validación que evita modificar los saldos de una caja existente"""
        if self.pk:  # La caja ya existe
            # Obtener los saldos originales de la base de datos
            try:
                original = Caja.objects.get(pk=self.pk)
                if self.saldo_caja != original.saldo_caja:
                    raise ValidationError({
                        'saldo_caja': 'No se puede modificar el saldo de caja de una caja existente. '
                                     'El saldo se actualiza automáticamente con los movimientos.'
                    })
            except Caja.DoesNotExist:
                pass

    def save(self, *args, **kwargs):
        """Guarda la caja con validaciones"""
        # Solo ejecutar validaciones si no es una operación de recálculo automático
        if not kwargs.pop('skip_validation', False):
            self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.nombre} - {'Activa' if self.activa else 'Inactiva'} - Saldo: {self.saldo_caja:.2f}€"

    def recalcular_saldo_caja(self):
        """
        Recalcula el saldo de efectivo basándose en todos los movimientos de caja.
        """
        total = Decimal('0.00')
        for movimiento in self.movimientos.all():
            total += movimiento.cantidad_real()
        
        self.saldo_caja = total
        self.save(skip_validation=True)
        return self.saldo_caja

    def recalcular_saldo(self):
        """
        Recalcula el saldo de la caja basándose en todos sus movimientos.
        Útil para corregir inconsistencias en los saldos.
        """
        total_caja = Decimal('0.00')
        for movimiento in self.movimientos.all():
            total_caja += movimiento.cantidad_real()
        
        self.saldo_caja = total_caja
        self.save(skip_validation=True)
        return self.saldo_caja

    def inicializar_desglose(self):
        """
        Inicializa el desglose de la caja con todas las denominaciones activas en 0
        """
        denominaciones = DenominacionEuro.objects.filter(activa=True)
        for denominacion in denominaciones:
            DesgloseCaja.objects.get_or_create(
                caja=self,
                denominacion=denominacion,
                defaults={'cantidad': 0},
                creado_por=self.creado_por
            )

    def actualizar_desglose_movimiento(self, movimiento_caja):
        """
        Actualiza el desglose de la caja basándose en un movimiento específico
        """
        for mov_dinero in movimiento_caja.movimientos_dinero.all():
            desglose, created = DesgloseCaja.objects.get_or_create(
                caja=self,
                denominacion=mov_dinero.denominacion,
                defaults={'cantidad': 0}
            )
            
            # Aplicar el cambio neto
            cantidad_neta = mov_dinero.cantidad_neta()
            desglose.cantidad += cantidad_neta
            
            # Asegurar que no sea negativo
            if desglose.cantidad < 0:
                desglose.cantidad = 0
            
            desglose.save()

    def obtener_desglose_actual(self):
        """
        Retorna el desglose actual de la caja
        """
        return self.desglose.select_related('denominacion').order_by('-denominacion__valor')

    def calcular_saldo_desde_desglose(self):
        """
        Calcula el saldo total basándose en el desglose actual
        """
        total = Decimal('0.00')
        for desglose in self.desglose.all():
            total += desglose.valor_total()
        return total

    def recalcular_desglose_completo(self):
        """
        Recalcula todo el desglose desde cero basándose en todos los movimientos
        """
        # Reinicializar desglose
        self.desglose.all().delete()
        self.inicializar_desglose()
        
        # Aplicar todos los movimientos en orden cronológico
        for movimiento in self.movimientos.order_by('fecha'):
            self.actualizar_desglose_movimiento(movimiento)

    class Meta:
        verbose_name = "Caja"
        verbose_name_plural = "Cajas"
        ordering = ['-nombre']


class Movimiento(UserTrackingMixin, models.Model):
    """
    Modelo abstracto para movimientos económicos (caja o banco).
    """
    concepto = models.ForeignKey(
        'Concepto',
        on_delete=models.PROTECT,
        verbose_name="Concepto"
    )

    cantidad = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Cantidad (€)"
    )

    fecha = models.DateTimeField(
        default=timezone.now,
        verbose_name="Fecha y hora del movimiento"
    )

    descripcion = models.TextField(
        verbose_name="Descripción",
        help_text="Descripción detallada del movimiento"
    )
    
    creado_por = models.ForeignKey(
        'auth.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Creado por",
        help_text="Usuario que creó este ejercicio"
    )

    creado_en = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Creado en",
        help_text="Fecha y hora de creación del ejercicio"
    )

    class Meta:
        abstract = True

    def es_gasto(self):
        """Determina si el movimiento es un gasto"""
        return self.concepto.es_gasto

    def cantidad_real(self):
        """Devuelve la cantidad con signo correcto para cálculos de saldo"""
        return -self.cantidad if self.es_gasto() else self.cantidad


class MovimientoCaja(Movimiento):
        
    ejercicio = models.ForeignKey(
        'Ejercicio',
        on_delete=models.CASCADE,
        verbose_name="Ejercicio",
        related_name="movimientos_caja"
    )
    
    caja = models.ForeignKey(
        Caja,
        on_delete=models.CASCADE,
        verbose_name="Caja",
        related_name="movimientos"
    )

    turno = models.ForeignKey(
        Turno,
        on_delete=models.CASCADE,
        verbose_name="Turno",
        related_name="movimientos"
    )

    justificante = models.CharField(
        max_length=5,
        blank=True,
        null=True,
        verbose_name="Nº Justificante"
    )

    archivo_justificante = models.FileField(
        upload_to='justificantes/',
        blank=True,
        null=True,
        verbose_name="Archivo justificante",
        help_text="Sube un PDF o imagen del justificante (opcional)"
    )

    def clean(self):
        """Validación de datos antes de guardar"""
        if self.cantidad <= 0:
            raise ValidationError("La cantidad debe ser positiva")
        
        if not self.caja.activa:
            raise ValidationError("No se pueden añadir movimientos a una caja inactiva")
        
        # Validar que los campos de justificante solo se usen para gastos
        if not self.concepto.es_gasto:
            # Para ingresos, los campos de justificante deben estar vacíos
            if self.justificante or self.archivo_justificante:
                raise ValidationError(
                    "Los campos de justificante solo pueden usarse para gastos, no para ingresos"
                )
        
        # Validar archivo justificante si se proporciona
        if self.archivo_justificante:
            import os
            ext = os.path.splitext(self.archivo_justificante.name)[1].lower()
            valid_extensions = ['.pdf', '.jpg', '.jpeg', '.png', '.gif', '.bmp']
            if ext not in valid_extensions:
                raise ValidationError(
                    f"El archivo debe ser una imagen (JPG, PNG, GIF, BMP) o un PDF. "
                    f"Extensión recibida: {ext}"
                )
            
            # Limitar tamaño de archivo a 10MB
            if self.archivo_justificante.size > 10 * 1024 * 1024:
                raise ValidationError("El archivo no puede superar los 10MB")
    
    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        super().delete(*args, **kwargs)

    def __str__(self):
        signo = "-" if self.es_gasto() else "+"
        return f"{self.fecha.strftime('%Y-%m-%d %H:%M')} | {self.caja.nombre} | {self.turno} | {signo}{self.cantidad:.2f}€ | {self.concepto}"

    class Meta:
        verbose_name = "Movimiento de caja"
        verbose_name_plural = "Movimientos de caja"
        ordering = ['-fecha']
        
        
class MovimientoCajaDeposito(UserTrackingMixin, models.Model):
    """
    Representa un movimiento de depósito en caja.
    """

    campamento = models.ForeignKey(
        'Campamento',
        on_delete=models.CASCADE,
        verbose_name="Campamento",
        related_name="movimientos_caja_deposito",
        help_text="Campamento al que pertenece este movimiento de depósito"
    )
    
    ejercicio = models.ForeignKey(
        'Ejercicio',
        on_delete=models.CASCADE,
        verbose_name="Ejercicio",
        related_name="movimientos_caja_deposito"
    )
    
    caja = models.ForeignKey(
        Caja,
        on_delete=models.CASCADE,
        verbose_name="Caja",
        related_name="movimientos_caja_deposito"
    )
    
    cantidad = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Cantidad (€)",
        help_text="Cantidad de dinero del movimiento de depósito"
    )
    
    fecha = models.DateTimeField(
        default=timezone.now,
        verbose_name="Fecha y hora del movimiento de depósito",
        help_text="Fecha y hora en que se realizó el movimiento de depósito"
    )
  
    creado_por = models.ForeignKey(
        'auth.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Creado por",
        help_text="Usuario que creó este movimiento de depósito"
    )
    
    creado_en = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Creado en",
        help_text="Fecha y hora de creación del movimiento de depósito"
    )
    
    def clean(self):
        """Validación de datos antes de guardar"""
        if self.cantidad <= 0:
            raise ValidationError("La cantidad debe ser positiva")
        
    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
        
    def __str__(self):
        return f"{self.fecha.strftime('%Y-%m-%d %H:%M')} | {self.caja.nombre} | +{self.cantidad:.2f}€"
    
    class Meta:
        verbose_name = "Movimiento de depósito en caja"
        verbose_name_plural = "Movimientos de depósito en caja"
        ordering = ['-fecha']
    
class MovimientoCajaRetiro(UserTrackingMixin, models.Model):
    """
    Representa un movimiento de retiro de caja.
    """

    campamento = models.ForeignKey(
        'Campamento',
        on_delete=models.CASCADE,
        verbose_name="Campamento",
        related_name="movimientos_caja_retiro",
        help_text="Campamento al que pertenece este movimiento de retiro"
    )
    
    ejercicio = models.ForeignKey(
        'Ejercicio',
        on_delete=models.CASCADE,
        verbose_name="Ejercicio",
        related_name="movimientos_caja_retiro"
    )
    
    caja = models.ForeignKey(
        Caja,
        on_delete=models.CASCADE,
        verbose_name="Caja",
        related_name="movimientos_caja_retiro"
    )
    
    cantidad = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Cantidad (€)",
        help_text="Cantidad de dinero del movimiento de retiro"
    )
    
    fecha = models.DateTimeField(
        default=timezone.now,
        verbose_name="Fecha y hora del movimiento de retiro",
        help_text="Fecha y hora en que se realizó el movimiento de retiro"
    )
  
    retirado_por = models.CharField(
        max_length=100,
        verbose_name="Retirado por",
        help_text="Nombre de la persona que realizó el retiro"
    )
    
    creado_por = models.ForeignKey(
        'auth.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Creado por",
        help_text="Usuario que creó este movimiento de retiro"
    )
    
    creado_en = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Creado en",
        help_text="Fecha y hora de creación del movimiento de retiro"
    )
    
    def clean(self):
        """Validación de datos antes de guardar"""
        if self.cantidad <= 0:
            raise ValidationError("La cantidad debe ser positiva")
        
        if not self.caja.activa:
            raise ValidationError("No se pueden añadir movimientos a una caja inactiva")
    
    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
        
    class Meta:
        verbose_name = "Movimiento de retiro en caja"
        verbose_name_plural = "Movimientos de retiro en caja"
        ordering = ['-fecha']
    

class MovimientoBanco(Movimiento):
    """
    Representa un movimiento bancario asociado a un ejercicio.
    Los movimientos bancarios afectan el saldo_banco del ejercicio, no de una caja específica.
    """
    
    campamento = models.ForeignKey(
        'Campamento',
        on_delete=models.CASCADE,
        verbose_name="Campamento",
        related_name="movimientos_banco",
        help_text="Campamento al que pertenece este movimiento bancario"
    )
    
    ejercicio = models.ForeignKey(
        'Ejercicio',
        on_delete=models.CASCADE,
        verbose_name="Ejercicio",
        related_name="movimientos_banco"
    )

    turno = models.ForeignKey(
        Turno,
        on_delete=models.CASCADE,
        verbose_name="Turno",
        related_name="movimientos_banco"
    )
    
    cuenta_bancaria = models.ForeignKey(
        'CuentaBancaria',
        on_delete=models.CASCADE,
        verbose_name="Cuenta bancaria",
        related_name="movimientos_banco"
    )
    
    via = models.ForeignKey(
        'ViaMovimientoBanco',
        on_delete=models.CASCADE,
        verbose_name="Vía de movimiento",
        related_name="movimientos_banco"
    )

    referencia_bancaria = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name="Referencia bancaria",
        help_text="Número de referencia de la operación bancaria"
    )

    archivo_justificante = models.FileField(
        upload_to='justificantes_banco/',
        blank=True,
        null=True,
        verbose_name="Archivo justificante",
        help_text="Sube un PDF o imagen del justificante (opcional)"
    )

    def clean(self):
        """Validación de datos antes de guardar"""
        if self.cantidad <= 0:
            raise ValidationError("La cantidad debe ser positiva")
        
        if not self.ejercicio.activo:
            raise ValidationError("No se pueden añadir movimientos a un ejercicio inactivo")
        
        # Validar archivo justificante si se proporciona
        if self.archivo_justificante:
            import os
            ext = os.path.splitext(self.archivo_justificante.name)[1].lower()
            valid_extensions = ['.pdf', '.jpg', '.jpeg', '.png', '.gif', '.bmp']
            if ext not in valid_extensions:
                raise ValidationError(
                    f"El archivo debe ser una imagen (JPG, PNG, GIF, BMP) o un PDF. "
                    f"Extensión recibida: {ext}"
                )
            
            # Limitar tamaño de archivo a 10MB
            if self.archivo_justificante.size > 10 * 1024 * 1024:
                raise ValidationError("El archivo no puede superar los 10MB")

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        super().delete(*args, **kwargs)

    def __str__(self):
        signo = "-" if self.es_gasto() else "+"
        return f"{self.fecha.strftime('%Y-%m-%d %H:%M')} | {self.ejercicio.nombre} | {signo}{self.cantidad:.2f}€ | {self.concepto}"

    class Meta:
        verbose_name = "Movimiento de banco"
        verbose_name_plural = "Movimientos de banco"
        ordering = ['-fecha']


class DenominacionEuro(UserTrackingMixin, models.Model):
    """
    Representa las diferentes denominaciones de euros (billetes y monedas)
    """
    valor = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        unique=True,
        verbose_name="Valor en euros"
    )
    
    es_billete = models.BooleanField(
        default=False,
        verbose_name="¿Es billete?",
        help_text="Si es False, se considera moneda"
    )
    
    activa = models.BooleanField(
        default=True,
        verbose_name="¿Denominación activa?",
        help_text="Solo las denominaciones activas aparecerán en los formularios"
    )
    
    creado_por = models.ForeignKey(
        'auth.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Creado por",
        help_text="Usuario que creó este ejercicio"
    )

    creado_en = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Creado en",
        help_text="Fecha y hora de creación del ejercicio"
    )
    
    def __str__(self):
        tipo = "billete" if self.es_billete else "moneda"
        return f"{self.valor}€ ({tipo})"
    
    class Meta:
        verbose_name = "Denominación Euro"
        verbose_name_plural = "Denominaciones Euro"
        ordering = ['-valor']


class DesgloseCaja(UserTrackingMixin, models.Model):
    """
    Representa la cantidad de cada denominación en una caja específica
    """
    caja = models.ForeignKey(
        'Caja',
        on_delete=models.CASCADE,
        verbose_name="Caja",
        related_name="desglose"
    )
    
    denominacion = models.ForeignKey(
        DenominacionEuro,
        on_delete=models.CASCADE,
        verbose_name="Denominación"
    )
    
    cantidad = models.PositiveIntegerField(
        default=0,
        verbose_name="Cantidad de unidades"
    )
    
    creado_por = models.ForeignKey(
        'auth.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Creado por",
        help_text="Usuario que creó este ejercicio"
    )

    creado_en = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Creado en",
        help_text="Fecha y hora de creación del ejercicio"
    )
    
    def valor_total(self):
        """Calcula el valor total de esta denominación"""
        return self.cantidad * self.denominacion.valor
    
    def __str__(self):
        return f"{self.caja.nombre} - {self.cantidad}x {self.denominacion}"
    
    class Meta:
        verbose_name = "Desglose de Caja"
        verbose_name_plural = "Desgloses de Caja"
        unique_together = [['caja', 'denominacion']]
        ordering = ['-denominacion__valor']


class MovimientoDinero(UserTrackingMixin, models.Model):
    """
    Representa el movimiento específico de denominaciones en un movimiento de caja
    """
    movimiento_caja = models.ForeignKey(
        'MovimientoCaja',
        on_delete=models.CASCADE,
        verbose_name="Movimiento de Caja",
        related_name="movimientos_dinero"
    )
    
    denominacion = models.ForeignKey(
        DenominacionEuro,
        on_delete=models.CASCADE,
        verbose_name="Denominación"
    )
    
    cantidad_entrada = models.PositiveIntegerField(
        default=0,
        verbose_name="Cantidad que entra",
        help_text="Billetes/monedas que entran a la caja"
    )
    
    cantidad_salida = models.PositiveIntegerField(
        default=0,
        verbose_name="Cantidad que sale",
        help_text="Billetes/monedas que salen de la caja (cambio)"
    )
    
    creado_por = models.ForeignKey(
        'auth.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Creado por",
        help_text="Usuario que creó este ejercicio"
    )

    creado_en = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Creado en",
        help_text="Fecha y hora de creación del ejercicio"
    )
    
    def cantidad_neta(self):
        """Calcula la cantidad neta (entrada - salida)"""
        return self.cantidad_entrada - self.cantidad_salida
    
    def valor_neto(self):
        """Calcula el valor neto del movimiento"""
        return self.cantidad_neta() * self.denominacion.valor
    
    def __str__(self):
        return f"{self.movimiento_caja} - {self.denominacion}: +{self.cantidad_entrada}/-{self.cantidad_salida}"
    
    class Meta:
        verbose_name = "Movimiento de Dinero"
        verbose_name_plural = "Movimientos de Dinero"
        unique_together = [['movimiento_caja', 'denominacion']]


class ViaMovimientoBanco(UserTrackingMixin, models.Model):
    """
    Representa el medio de un movimiento bancario
    """

    nombre = models.CharField(
        max_length=100,
        verbose_name="Nombre de la vía de movimiento bancario",
        help_text="Ej: 'Bizum', 'Transferencia', etc.",
    )

    creado_por = models.ForeignKey(
        'auth.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Creado por",
        help_text="Usuario que creó esta vía de movimiento bancario"
    )

    creado_en = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Creado en",
        help_text="Fecha y hora de creación de la vía"
    )

    def __str__(self):
        return self.nombre

    class Meta:
        verbose_name = "Vía de Movimiento Bancario"
        verbose_name_plural = "Vías de Movimiento Bancario"


class CuentaBancaria(UserTrackingMixin, models.Model):
    """
    Representa una cuenta bancaria concreta.
    """
    
    nombre = models.CharField(
        max_length=100,
        unique=True,
        verbose_name="Nombre de la cuenta",
        help_text="Ej: 'Asociación la Forja'"
    )

    titular = models.CharField(
        max_length=100,
        verbose_name="Titular",
        help_text="Nombre del titular de la cuenta"
    )

    IBAN = models.CharField(
        max_length=34,
        unique=True,
        verbose_name="IBAN",
        help_text="Número de cuenta IBAN"
    )

    activo = models.BooleanField(
        default=True,
        verbose_name="¿Cuenta activa?",
        help_text="Marca si esta cuenta está actualmente en uso"
    )
    
    creado_por = models.ForeignKey(
        'auth.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Creado por",
        help_text="Usuario que creó esta cuenta"
    )

    creado_en = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Creado en",
        help_text="Fecha y hora de creación de la cuenta"
    )

    def __str__(self):
        return f"{self.nombre} - *{self.IBAN[-4:]}" 

    class Meta:
        verbose_name = "Cuenta Bancaria"
        verbose_name_plural = "Cuentas Bancarias"
        ordering = ['nombre']
    
    
class Campamento(UserTrackingMixin, models.Model):
    """
    Representa un campamento específico.
    """

    nombre = models.CharField(
        max_length=100,
        unique=True,
        verbose_name="Nombre del campamento"
    )
    
    creado_por = models.ForeignKey(
        'auth.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Creado por",
        help_text="Usuario que creó este campamento"
    )

    creado_en = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Creado en",
        help_text="Fecha y hora de creación del campamento"
    )

    def __str__(self):
        return f"{self.nombre}"

    class Meta:
        verbose_name = "Campamento"
        verbose_name_plural = "Campamentos"
        ordering = ['nombre']


@receiver(post_save, sender=MovimientoBanco)
def actualizar_saldo_banco_on_save(sender, instance, created, **kwargs):
    """Actualiza el saldo bancario del ejercicio cuando se crea un movimiento de banco"""
    if created:
        # Actualizar saldo bancario del ejercicio
        instance.ejercicio.saldo_banco += instance.cantidad_real()
        instance.ejercicio.save()


@receiver(pre_delete, sender=MovimientoBanco)
def actualizar_saldo_banco_on_delete(sender, instance, **kwargs):
    """Actualiza el saldo bancario del ejercicio cuando se elimina un movimiento de banco"""
    # Revertir el movimiento bancario del ejercicio
    instance.ejercicio.saldo_banco -= instance.cantidad_real()
    instance.ejercicio.save()


# Señales Django para actualizar el saldo de la caja automáticamente
@receiver(post_save, sender=MovimientoCaja)
def actualizar_saldo_caja_on_save(sender, instance, created, **kwargs):
    """Actualiza el saldo de caja cuando se crea un movimiento de caja"""
    if created:
        # Actualizar saldo de caja
        instance.caja.saldo_caja += instance.cantidad_real()
        instance.caja.save(skip_validation=True)


@receiver(pre_delete, sender=MovimientoCaja)
def actualizar_saldo_caja_on_delete(sender, instance, **kwargs):
    """Actualiza el saldo de caja cuando se elimina un movimiento de caja""" 
    # Actualizar saldo de caja
    instance.caja.saldo_caja -= instance.cantidad_real()
    instance.caja.save(skip_validation=True)


@receiver(post_save, sender=MovimientoDinero)
def actualizar_desglose_on_movimiento_dinero_save(sender, instance, created, **kwargs):
    """Actualiza el desglose cuando se crea o modifica un MovimientoDinero"""
    if created:
        desglose, created_desglose = DesgloseCaja.objects.get_or_create(
            caja=instance.movimiento_caja.caja,
            denominacion=instance.denominacion,
            defaults={'cantidad': 0}
        )
        
        desglose.cantidad += instance.cantidad_neta()
        if desglose.cantidad < 0:
            desglose.cantidad = 0
        desglose.save()


@receiver(post_delete, sender=MovimientoDinero)
def actualizar_desglose_on_movimiento_dinero_delete(sender, instance, **kwargs):
    """Actualiza el desglose cuando se elimina un MovimientoDinero"""
    desglose = DesgloseCaja.objects.filter(
        caja=instance.movimiento_caja.caja,
        denominacion=instance.denominacion
    ).first()
    if desglose:
        desglose.cantidad -= instance.cantidad_neta()
        if desglose.cantidad < 0:
            desglose.cantidad = 0
        desglose.save()


@receiver(post_save, sender=Caja)
def inicializar_desglose_caja(sender, instance, created, **kwargs):
    """Inicializa el desglose cuando se crea una nueva caja"""
    if created:
        instance.inicializar_desglose()


@receiver(post_save, sender=DesgloseCaja)
def actualizar_saldo_on_desglose_save(sender, instance, created, **kwargs):
    """Actualiza el saldo de caja cuando se modifica el desglose"""
    # Calcular el nuevo saldo basado en el desglose total
    nuevo_saldo_caja = instance.caja.calcular_saldo_desde_desglose()
    
    # Actualizar el saldo de caja
    if instance.caja.saldo_caja != nuevo_saldo_caja:
        instance.caja.saldo_caja = nuevo_saldo_caja
        instance.caja.save(skip_validation=True)


@receiver(post_delete, sender=DesgloseCaja)
def actualizar_saldo_on_desglose_delete(sender, instance, **kwargs):
    """Actualiza el saldo de caja cuando se elimina un desglose"""
    # Calcular el nuevo saldo basado en el desglose restante
    nuevo_saldo_caja = instance.caja.calcular_saldo_desde_desglose()
    
    # Actualizar el saldo de caja
    if instance.caja.saldo_caja != nuevo_saldo_caja:
        instance.caja.saldo_caja = nuevo_saldo_caja
        instance.caja.save(skip_validation=True)
