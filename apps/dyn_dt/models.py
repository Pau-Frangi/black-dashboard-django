from django.db import models
from decimal import Decimal
from django.utils.translation import gettext_lazy as _
from datetime import date
from django.core.exceptions import ValidationError

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
    """

    nombre = models.CharField(
        max_length=100,
        unique=True,
        verbose_name="Nombre del turno"
    )

    def __str__(self):
        return self.nombre

    class Meta:
        verbose_name = "Turno"
        verbose_name_plural = "Turnos"
        ordering = ['nombre']



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
        verbose_name="Saldo actual"
    )

    observaciones = models.TextField(
        blank=True,
        null=True,
        verbose_name="Observaciones"
    )

    def __str__(self):
        return f"{self.nombre} ({self.año}) - Saldo: {self.saldo:.2f}€"

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

    fecha = models.DateField(
        default=date.today,
        verbose_name="Fecha del movimiento"
    )

    justificante = models.CharField(
        max_length=5,
        blank=True,
        null=True,
        verbose_name="Nº Justificante"
    )

    observaciones = models.TextField(
        blank=True,
        null=True,
        verbose_name="Observaciones"
    )

    def clean(self):
        """Validación de datos antes de guardar"""
        if self.cantidad <= 0:
            raise ValidationError("La cantidad debe ser positiva")
        
        if not self.caja.activa:
            raise ValidationError("No se pueden añadir movimientos a una caja inactiva")

    def save(self, *args, **kwargs):
        """Actualiza el saldo de la caja al guardar"""
        if not self.pk:  # Solo para nuevos movimientos
            self.full_clean()  # Ejecuta las validaciones
            
            # Actualizar el saldo de la caja
            self.caja.saldo += self.cantidad_real()
            self.caja.save()
        
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        """Actualiza el saldo de la caja al eliminar"""
        # Restar el movimiento del saldo antes de eliminar
        self.caja.saldo -= self.cantidad_real()
        self.caja.save()
        super().delete(*args, **kwargs)

    def es_gasto(self):
        """Determina si el movimiento es un gasto"""
        return self.concepto.es_gasto

    def cantidad_real(self):
        """Devuelve la cantidad con signo correcto para cálculos de saldo"""
        return -self.cantidad if self.es_gasto() else self.cantidad

    def __str__(self):
        signo = "-" if self.es_gasto() else "+"
        return f"{self.fecha} | {self.caja.nombre} | {self.turno} | {signo}{self.cantidad:.2f}€ | {self.concepto}"

    class Meta:
        verbose_name = "Movimiento de caja"
        verbose_name_plural = "Movimientos de caja"
        ordering = ['-fecha']