from django.db import models
from decimal import Decimal
from django.utils.translation import gettext_lazy as _
from datetime import date
from django.core.exceptions import ValidationError
from django.db.models.signals import post_save, pre_delete, post_delete
from django.dispatch import receiver
from django.utils import timezone

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





class Turno(models.Model):
    """
    Representa un turno del campamento (por ejemplo: 'Primer turno chicas').
    Cada turno debe estar asociado a una caja específica.
    """
    
    caja = models.ForeignKey(
        'Caja',
        on_delete=models.CASCADE,
        verbose_name="Caja",
        related_name="turnos",
        help_text="Caja a la que pertenece este turno"
    )

    nombre = models.CharField(
        max_length=100,
        verbose_name="Nombre del turno"
    )

    def __str__(self):
        return f"{self.nombre} ({self.caja.nombre})"

    class Meta:
        verbose_name = "Turno"
        verbose_name_plural = "Turnos"
        ordering = ['caja__nombre', 'nombre']
        unique_together = [['caja', 'nombre']]  # Unique turno name per caja



class Concepto(models.Model):
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

    def __str__(self):
        return f"{self.nombre} {'*' if self.es_gasto else ''}"

    class Meta:
        verbose_name = "Concepto"
        verbose_name_plural = "Conceptos"
        ordering = ['nombre']

        

class Caja(models.Model):
    """
    Representa una caja general para un año o una campaña económica.
    Por ejemplo: 'Caja 2025'.
    """
    nombre = models.CharField(
        max_length=100,
        unique=True,
        verbose_name="Nombre de la caja",
        help_text="Ej: 'Caja 2025'"
    )

    año = models.PositiveIntegerField(
        verbose_name="Año",
        help_text="Año correspondiente a esta caja (ej. 2025)"
    )

    activa = models.BooleanField(
        default=True,
        verbose_name="¿Caja activa?",
        help_text="Marca si esta caja está actualmente en uso"
    )

    saldo = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name="Saldo inicial/actual",
        help_text="Solo se puede modificar al crear la caja. Después se actualiza automáticamente con los movimientos."
    )

    observaciones = models.TextField(
        blank=True,
        null=True,
        verbose_name="Observaciones"
    )

    def clean(self):
        """Validación que evita modificar el saldo de una caja existente"""
        if self.pk:  # La caja ya existe
            # Obtener el saldo original de la base de datos
            try:
                original = Caja.objects.get(pk=self.pk)
                if self.saldo != original.saldo:
                    raise ValidationError({
                        'saldo': 'No se puede modificar el saldo de una caja existente. '
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
        return f"{self.nombre} ({self.año}) - Saldo: {self.saldo:.2f}€"

    def recalcular_saldo(self):
        """
        Recalcula el saldo de la caja basándose en todos sus movimientos.
        Útil para corregir inconsistencias en el saldo.
        """
        total = Decimal('0.00')
        for movimiento in self.movimientos.all():
            total += movimiento.cantidad_real()
        
        self.saldo = total
        self.save(skip_validation=True)  # Saltamos la validación para el recálculo automático
        return self.saldo

    class Meta:
        verbose_name = "Caja"
        verbose_name_plural = "Cajas"
        ordering = ['-año']
        
        


class MovimientoCaja(models.Model):
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

    concepto = models.ForeignKey(
        Concepto,
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

    descripcion = models.TextField(
        verbose_name="Descripción",
        help_text="Descripción detallada del movimiento"
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
        """Valida los datos antes de guardar"""
        self.full_clean()  # Ejecuta las validaciones
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        """Elimina el movimiento"""
        super().delete(*args, **kwargs)

    def es_gasto(self):
        """Determina si el movimiento es un gasto"""
        return self.concepto.es_gasto

    def cantidad_real(self):
        """Devuelve la cantidad con signo correcto para cálculos de saldo"""
        return -self.cantidad if self.es_gasto() else self.cantidad

    def __str__(self):
        signo = "-" if self.es_gasto() else "+"
        return f"{self.fecha.strftime('%Y-%m-%d %H:%M')} | {self.caja.nombre} | {self.turno} | {signo}{self.cantidad:.2f}€ | {self.concepto}"

    class Meta:
        verbose_name = "Movimiento de caja"
        verbose_name_plural = "Movimientos de caja"
        ordering = ['-fecha']


# Señales Django para actualizar el saldo de la caja automáticamente
@receiver(post_save, sender=MovimientoCaja)
def actualizar_saldo_on_save(sender, instance, created, **kwargs):
    """
    Actualiza el saldo de la caja cuando se guarda un MovimientoCaja.
    Solo se ejecuta para nuevos movimientos (created=True).
    """
    if created:
        # Actualizar el saldo de la caja
        instance.caja.saldo += instance.cantidad_real()
        instance.caja.save(skip_validation=True)


@receiver(pre_delete, sender=MovimientoCaja)
def actualizar_saldo_on_delete(sender, instance, **kwargs):
    """
    Actualiza el saldo de la caja cuando se elimina un MovimientoCaja.
    Se ejecuta antes de eliminar para que el objeto aún exista.
    """
    # Restar el movimiento del saldo antes de eliminar
    instance.caja.saldo -= instance.cantidad_real()
    instance.caja.save(skip_validation=True)