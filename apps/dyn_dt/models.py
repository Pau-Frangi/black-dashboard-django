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

    saldo_caja = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name="Saldo de caja (efectivo)",
        help_text="Saldo de los movimientos en efectivo. Se actualiza automáticamente."
    )

    saldo_banco = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name="Saldo bancario",
        help_text="Saldo de los movimientos bancarios. Se actualiza automáticamente."
    )

    # Campo legacy para compatibilidad
    saldo = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name="Saldo total",
        help_text="Suma del saldo de caja y banco. Se calcula automáticamente."
    )

    observaciones = models.TextField(
        blank=True,
        null=True,
        verbose_name="Observaciones"
    )

    def clean(self):
        """Validación que evita modificar los saldos de una caja existente"""
        if self.pk:  # La caja ya existe
            # Obtener los saldos originales de la base de datos
            try:
                original = Caja.objects.get(pk=self.pk)
                if (self.saldo_caja != original.saldo_caja or 
                    self.saldo_banco != original.saldo_banco or 
                    self.saldo != original.saldo):
                    raise ValidationError({
                        'saldo_caja': 'No se puede modificar el saldo de caja de una caja existente. '
                                     'El saldo se actualiza automáticamente con los movimientos.',
                        'saldo_banco': 'No se puede modificar el saldo bancario de una caja existente. '
                                      'El saldo se actualiza automáticamente con los movimientos.',
                        'saldo': 'No se puede modificar el saldo total de una caja existente. '
                                'El saldo se calcula automáticamente.'
                    })
            except Caja.DoesNotExist:
                pass

    def save(self, *args, **kwargs):
        """Guarda la caja con validaciones"""
        # Calcular el saldo total antes de guardar
        if not kwargs.get('skip_validation', False):
            self.saldo = self.saldo_caja + self.saldo_banco
        
        # Solo ejecutar validaciones si no es una operación de recálculo automático
        if not kwargs.pop('skip_validation', False):
            self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.nombre} ({self.año}) - Efectivo: {self.saldo_caja:.2f}€ | Banco: {self.saldo_banco:.2f}€ | Total: {self.saldo:.2f}€"

    def recalcular_saldo_caja(self):
        """
        Recalcula el saldo de efectivo basándose en todos los movimientos de caja.
        """
        total = Decimal('0.00')
        for movimiento in self.movimientos.all():
            total += movimiento.cantidad_real()
        
        self.saldo_caja = total
        self.saldo = self.saldo_caja + self.saldo_banco
        self.save(skip_validation=True)
        return self.saldo_caja

    def recalcular_saldo_banco(self):
        """
        Recalcula el saldo bancario basándose en todos los movimientos de banco.
        """
        total = Decimal('0.00')
        for movimiento in self.movimientos_banco.all():
            total += movimiento.cantidad_real()
        
        self.saldo_banco = total
        self.saldo = self.saldo_caja + self.saldo_banco
        self.save(skip_validation=True)
        return self.saldo_banco

    def recalcular_saldo(self):
        """
        Recalcula ambos saldos de la caja basándose en todos sus movimientos.
        Útil para corregir inconsistencias en los saldos.
        """
        total_caja = Decimal('0.00')
        for movimiento in self.movimientos.all():
            total_caja += movimiento.cantidad_real()
        
        total_banco = Decimal('0.00')
        for movimiento in self.movimientos_banco.all():
            total_banco += movimiento.cantidad_real()
        
        self.saldo_caja = total_caja
        self.saldo_banco = total_banco
        self.saldo = self.saldo_caja + self.saldo_banco
        self.save(skip_validation=True)
        return self.saldo

    def inicializar_desglose(self):
        """
        Inicializa el desglose de la caja con todas las denominaciones activas en 0
        """
        denominaciones = DenominacionEuro.objects.filter(activa=True)
        for denominacion in denominaciones:
            DesgloseCaja.objects.get_or_create(
                caja=self,
                denominacion=denominacion,
                defaults={'cantidad': 0}
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


class MovimientoBanco(models.Model):
    """
    Representa un movimiento bancario (transferencias, cheques, domiciliaciones, etc.)
    Tiene los mismos campos que MovimientoCaja pero sin desglose de billetes/monedas
    """
    caja = models.ForeignKey(
        Caja,
        on_delete=models.CASCADE,
        verbose_name="Caja",
        related_name="movimientos_banco"
    )

    turno = models.ForeignKey(
        Turno,
        on_delete=models.CASCADE,
        verbose_name="Turno",
        related_name="movimientos_banco"
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
        upload_to='justificantes_banco/',
        blank=True,
        null=True,
        verbose_name="Archivo justificante",
        help_text="Sube un PDF o imagen del justificante (opcional)"
    )

    descripcion = models.TextField(
        verbose_name="Descripción",
        help_text="Descripción detallada del movimiento bancario"
    )

    # Campos específicos para movimientos bancarios
    referencia_bancaria = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name="Referencia bancaria",
        help_text="Número de referencia de la operación bancaria"
    )

    def clean(self):
        """Validación de datos antes de guardar"""
        if self.cantidad <= 0:
            raise ValidationError("La cantidad debe ser positiva")
        
        if not self.caja.activa:
            raise ValidationError("No se pueden añadir movimientos a una caja inactiva")
        
        # Para movimientos bancarios, tanto gastos como ingresos pueden tener justificante
        # No se aplica la restricción de justificante solo para gastos
        
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
        verbose_name = "Movimiento de banco"
        verbose_name_plural = "Movimientos de banco"
        ordering = ['-fecha']





class DenominacionEuro(models.Model):
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
    
    def __str__(self):
        tipo = "billete" if self.es_billete else "moneda"
        return f"{self.valor}€ ({tipo})"
    
    class Meta:
        verbose_name = "Denominación Euro"
        verbose_name_plural = "Denominaciones Euro"
        ordering = ['-valor']


class DesgloseCaja(models.Model):
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


class MovimientoDinero(models.Model):
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


# Señales Django para actualizar el saldo de la caja automáticamente
@receiver(post_save, sender=MovimientoCaja)
def actualizar_saldo_caja_on_save(sender, instance, created, **kwargs):
    """Actualiza el saldo de caja cuando se crea un movimiento de caja"""
    if created:
        # Actualizar saldo de caja
        instance.caja.saldo_caja += instance.cantidad_real()
        instance.caja.saldo = instance.caja.saldo_caja + instance.caja.saldo_banco
        instance.caja.save(skip_validation=True)


@receiver(pre_delete, sender=MovimientoCaja)
def actualizar_saldo_caja_on_delete(sender, instance, **kwargs):
    """Actualiza el saldo de caja cuando se elimina un movimiento de caja"""
    # Revertir el movimiento del desglose antes de eliminar
    for mov_dinero in instance.movimientos_dinero.all():
        desglose = DesgloseCaja.objects.filter(
            caja=instance.caja,
            denominacion=mov_dinero.denominacion
        ).first()
        
        if desglose:
            # Revertir el cambio
            desglose.cantidad -= mov_dinero.cantidad_neta()
            if desglose.cantidad < 0:
                desglose.cantidad = 0
            desglose.save()
    
    # Actualizar saldo de caja
    instance.caja.saldo_caja -= instance.cantidad_real()
    instance.caja.saldo = instance.caja.saldo_caja + instance.caja.saldo_banco
    instance.caja.save(skip_validation=True)


@receiver(post_save, sender=MovimientoBanco)
def actualizar_saldo_banco_on_save(sender, instance, created, **kwargs):
    """Actualiza el saldo bancario cuando se crea un movimiento de banco"""
    if created:
        # Actualizar saldo bancario
        instance.caja.saldo_banco += instance.cantidad_real()
        instance.caja.saldo = instance.caja.saldo_caja + instance.caja.saldo_banco
        instance.caja.save(skip_validation=True)


@receiver(pre_delete, sender=MovimientoBanco)
def actualizar_saldo_banco_on_delete(sender, instance, **kwargs):
    """Actualiza el saldo bancario cuando se elimina un movimiento de banco"""
    # Actualizar saldo bancario
    instance.caja.saldo_banco -= instance.cantidad_real()
    instance.caja.saldo = instance.caja.saldo_caja + instance.caja.saldo_banco
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
        instance.caja.saldo = instance.caja.saldo_caja + instance.caja.saldo_banco
        instance.caja.save(skip_validation=True)


@receiver(post_delete, sender=DesgloseCaja)
def actualizar_saldo_on_desglose_delete(sender, instance, **kwargs):
    """Actualiza el saldo de caja cuando se elimina un desglose"""
    # Calcular el nuevo saldo basado en el desglose restante
    nuevo_saldo_caja = instance.caja.calcular_saldo_desde_desglose()
    
    # Actualizar el saldo de caja
    if instance.caja.saldo_caja != nuevo_saldo_caja:
        instance.caja.saldo_caja = nuevo_saldo_caja
        instance.caja.saldo = instance.caja.saldo_caja + instance.caja.saldo_banco
        instance.caja.save(skip_validation=True)