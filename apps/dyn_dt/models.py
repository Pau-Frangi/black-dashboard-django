from django.db import models
from decimal import Decimal
from django.utils.translation import gettext_lazy as _
from .mixins import UserTrackingMixin



class UserTrackedModel(UserTrackingMixin, models.Model):
    
    creado_por = models.ForeignKey(
        'auth.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Creado por",
        help_text="Usuario que creó este registro"
    )
    
    creado_en = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Creado en",
        help_text="Fecha y hora de creación del registro"
    )
    
    modificado_por = models.ForeignKey(
        'auth.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='%(class)s_modificado_por',
        verbose_name="Modificado por",
        help_text="Usuario que modificó este registro"
    )
    
    modificado_en = models.DateTimeField(
        auto_now=True,
        verbose_name="Modificado en",
        help_text="Fecha y hora de la última modificación del registro"
    )
    
    class Meta:
        abstract = True
        ordering = ['-creado_en']
                

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


class Ejercicio(UserTrackedModel, models.Model):
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

    descripcion = models.TextField(
        blank=True,
        null=True,
        verbose_name="Descripción",
        help_text="Descripción adicional del ejercicio"
    )
    
    def calcular_resultado_caja_ejercicio(self, campamento=None):
        """
        Calcula la suma del importe de todos los movimientos de caja asociados a este ejercicio.
        """
        from apps.caja.models import MovimientoCajaIngreso, MovimientoCajaGasto
        ingresos = MovimientoCajaIngreso.objects.filter(ejercicio=self, caja__campamento=campamento)
        gastos = MovimientoCajaGasto.objects.filter(ejercicio=self, caja__campamento=campamento)
        total = Decimal('0.00')
        for ingreso in ingresos:
            total += ingreso.importe
        for gasto in gastos:
            total -= gasto.importe
        return total

    def calcular_resultado_banco_ejercicio(self, campamento=None):
        """
        Calcula la suma del importe de todos los movimientos bancarios asociados a este ejercicio.
        """
        from apps.banco.models import MovimientoBancoIngreso, MovimientoBancoGasto
        ingresos = MovimientoBancoIngreso.objects.filter(ejercicio=self, campamento=campamento)
        gastos = MovimientoBancoGasto.objects.filter(ejercicio=self, campamento=campamento)
        total = Decimal('0.00')
        for ingreso in ingresos:
            total += ingreso.importe
        for gasto in gastos:
            total -= gasto.importe
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
        Calcula la suma de todos los movimientos de caja de los ejercicios desde el primer año hasta el actual.
        """
        from apps.caja.models import MovimientoCajaDeposito, MovimientoCajaRetirada
        total = Decimal('0.00')
        for ejercicio in Ejercicio.objects.filter(año__lte=self.año):
            total += ejercicio.calcular_resultado_caja_ejercicio(campamento=campamento)
            # Sumar los importes de los MovimientoCajaDeposito
            depositos = MovimientoCajaDeposito.objects.filter(ejercicio=ejercicio, caja__campamento=campamento)
            for deposito in depositos:
                total += deposito.importe
            # Restar los importes de los MovimientoCajaRetirada
            retiradas = MovimientoCajaRetirada.objects.filter(ejercicio=ejercicio, caja__campamento=campamento)
            for retirada in retiradas:
                total -= retirada.importe
            # Las transferencias entre cajas no afectan al saldo total de las cajas
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

    def __str__(self):
        return f"{self.nombre} ({self.año}) - Total: {self.saldo_total:.2f}€"

    class Meta:
        verbose_name = "Ejercicio"
        verbose_name_plural = "Ejercicios"
        ordering = ['-año']




class Turno(UserTrackedModel, models.Model):
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

    def __str__(self):
        return f"{self.nombre} ({self.ejercicio.nombre}) - {self.campamento.nombre})"

    class Meta:
        verbose_name = "Turno"
        verbose_name_plural = "Turnos"
        ordering = ['ejercicio__nombre', 'nombre']
        unique_together = [['ejercicio', 'nombre']]  # Unique turno name per ejercicio



class Concepto(UserTrackedModel, models.Model):
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
        return self.nombre

    class Meta:
        verbose_name = "Concepto"
        verbose_name_plural = "Conceptos"
        ordering = ['nombre']
   
    
class Campamento(UserTrackedModel, models.Model):
    """
    Representa un campamento específico.
    """

    nombre = models.CharField(
        max_length=100,
        unique=True,
        verbose_name="Nombre del campamento"
    )

    def __str__(self):
        return f"{self.nombre}"

    class Meta:
        verbose_name = "Campamento"
        verbose_name_plural = "Campamentos"
        ordering = ['nombre']

