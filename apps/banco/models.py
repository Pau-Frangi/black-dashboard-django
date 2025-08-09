from django.db import models
from pydantic import ValidationError
from apps.dyn_dt.models import UserTrackedModel, Turno, Ejercicio, Concepto, Campamento
from django.utils import timezone
from decimal import Decimal


class CuentaBancaria(UserTrackedModel, models.Model):
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

    def __str__(self):
        return f"{self.nombre} - *{self.IBAN[-4:]}" 

    class Meta:
        verbose_name = "Cuenta Bancaria"
        verbose_name_plural = "Cuentas Bancarias"
        ordering = ['nombre']
    
    
    def calcular_ingresos(self):
        """
        Calcula el importe total de MovimientosBancoIngreso asociados a esta cuenta.
        """
        ingresos = MovimientoBancoIngreso.objects.filter(cuenta_bancaria=self)
        return sum(ingreso.importe for ingreso in ingresos) if ingresos else Decimal('0.00')
    
    def calcular_gastos(self):
        """
        Calcula el importe total de MovimientosBancoGasto asociados a esta cuenta.
        """
        gastos = MovimientoBancoGasto.objects.filter(cuenta_bancaria=self)
        return sum(gasto.importe for gasto in gastos) if gastos else Decimal('0.00')

    def calcular_saldo(self):
        """
        Calcula el saldo total de la cuenta.
        El saldo se calcula como:
        Saldo = Ingresos - Gastos
        """
        return self.calcular_ingresos() - self.calcular_gastos()
    

class ViaMovimientoBanco(UserTrackedModel, models.Model):
    """
    Representa el medio de un movimiento bancario
    """

    nombre = models.CharField(
        max_length=100,
        verbose_name="Nombre de la vía de movimiento bancario",
        help_text="Ej: 'Bizum', 'Transferencia', etc.",
    )

    def __str__(self):
        return self.nombre

    class Meta:
        verbose_name = "Vía de Movimiento Bancario"
        verbose_name_plural = "Vías de Movimiento Bancario"

    

class MovimientoBanco(UserTrackedModel, models.Model):
    
    """
    Modelo abstracto para movimientos económicos (de banco).
    """ 
    
    importe = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Importe (€)"
    )

    fecha = models.DateTimeField(
        default=timezone.now,
        verbose_name="Fecha y hora del movimiento"
    )

    descripcion = models.TextField(
        verbose_name="Descripción",
        help_text="Descripción detallada del movimiento"
    )
    
    referencia_bancaria = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name="Referencia bancaria",
        help_text="Número de referencia de la operación bancaria"
    )

    class Meta:
        abstract = True

    def clean(self):
        """Validación de datos antes de guardar"""
        if self.importe <= 0:
            raise ValidationError("La cantidad debe ser positiva")
        
    def serializar(self):
        return {
            "id": self.id,
            "importe": self.importe,
            "fecha": self.fecha,
            'fecha_completa': self.fecha.strftime('%Y-%m-%d %H:%M:%S'),
            'fecha_display': self.fecha.strftime('%d/%m/%Y %H:%M'),
            'datetime_iso': self.fecha.isoformat(),
            "descripcion": self.descripcion,
            "referencia_bancaria": self.referencia_bancaria or "",
            "canal_movimiento": "banco"
        }


class MovimientoBancoIngreso(MovimientoBanco):
    """
    Modelo para registrar ingresos en el banco.
    """
    ejercicio = models.ForeignKey(
        Ejercicio,
        on_delete=models.CASCADE,
        verbose_name="Ejercicio",
        related_name="movimientos_banco_ingreso",
    )
    
    campamento = models.ForeignKey(
        Campamento,
        on_delete=models.CASCADE,
        verbose_name="Campamento",
        related_name="movimientos_banco_ingreso"
    )
    
    cuenta_bancaria = models.ForeignKey(
        CuentaBancaria,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name="Cuenta Bancaria",
        related_name="movimientos_banco_ingreso"
    )
    
    turno = models.ForeignKey(
        Turno,
        on_delete=models.CASCADE,
        verbose_name="Turno",
        related_name="movimientos_banco_ingreso"
    )

    concepto = models.ForeignKey(
        Concepto,
        on_delete=models.PROTECT,
        verbose_name="Concepto",
        related_name="movimientos_banco_ingreso",
        help_text="Concepto del movimiento de ingreso (ej. 'Inscripciones', 'Donación', etc.)"
    )
      
    cuenta_bancaria = models.ForeignKey(
        CuentaBancaria,
        on_delete=models.CASCADE,
        verbose_name="Cuenta bancaria",
        related_name="movimientos_banco_ingreso",
    )
    
    via = models.ForeignKey(
        ViaMovimientoBanco,
        on_delete=models.CASCADE,
        verbose_name="Vía de movimiento",
        related_name="movimientos_banco_ingreso"
    )

    archivo = models.FileField(
        upload_to='movimientos_ingreso/',
        null=True,
        blank=True,
        verbose_name="Archivo adjunto",
        help_text="Archivo justificante del movimiento de ingreso"
    )

    class Meta:
        verbose_name = "Movimiento de Ingreso"
        verbose_name_plural = "Movimientos de Ingreso"

    def __str__(self):
        return f"Ingreso de {self.importe} € en {self.cuenta_bancaria} el {self.fecha}"
    
    def serializar(self):
        data = super().serializar()
        data.update({
            "ejercicio_id": self.ejercicio.id,
            "ejercicio": self.ejercicio.nombre,
            "campamento_id": self.campamento.id,
            "campamento": self.campamento.nombre,
            "cuenta_bancaria_id": self.cuenta_bancaria.id if self.cuenta_bancaria else None,
            "cuenta_bancaria": str(self.cuenta_bancaria),
            "turno_id": self.turno.id,
            "turno": str(self.turno),
            "concepto_id": self.concepto.id,
            "concepto": str(self.concepto),
            "via_id": self.via.id,
            "via": str(self.via),
            "archivo": self.archivo.url if self.archivo else None,
            "tipo_operacion": "ingreso"
        })
        return data


class MovimientoBancoGasto(MovimientoBanco):
    """
    Modelo para registrar gastos en el banco.
    """
    
    ejercicio = models.ForeignKey(
        Ejercicio,
        on_delete=models.CASCADE,
        verbose_name="Ejercicio",
        related_name="movimientos_banco_gasto",
        help_text="Ejercicio al que pertenece este movimiento de gasto"
    )
    
    campamento = models.ForeignKey(
        Campamento,
        on_delete=models.CASCADE,
        verbose_name="Campamento",
        related_name="movimientos_banco_gasto"
    )
    
    cuenta_bancaria = models.ForeignKey(
        CuentaBancaria,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name="Cuenta Bancaria",
        related_name="movimientos_banco_gasto"
    )
    
    turno = models.ForeignKey(
        Turno,
        on_delete=models.CASCADE,
        verbose_name="Turno",
        related_name="movimientos_banco_gasto",
        help_text="Turno al que pertenece este movimiento de gasto"
    )

    concepto = models.ForeignKey(
        Concepto,
        on_delete=models.PROTECT,
        verbose_name="Concepto",
        related_name="movimientos_banco_gasto",
        help_text="Concepto del movimiento de gasto (ej. 'Compra de comida', 'Materiales', etc.)"
    )

    archivo = models.FileField(
        upload_to='movimientos_gasto/',
        null=True,
        blank=True,
        verbose_name="Archivo adjunto",
        help_text="Archivo de factura del movimiento de gasto"
    )

    class Meta:
        verbose_name = "Movimiento de Gasto"
        verbose_name_plural = "Movimientos de Gasto"

    def __str__(self):
        return f"Gasto de {self.importe} € en {self.cuenta_bancaria} el {self.fecha}"
    
    
    def serializar(self):
        data = super().serializar()
        data.update({
            "ejercicio_id": self.ejercicio.id,
            "ejercicio": self.ejercicio.nombre,
            "campamento_id": self.campamento.id,
            "campamento": self.campamento.nombre,
            "cuenta_bancaria_id": self.cuenta_bancaria.id if self.cuenta_bancaria else None,
            "cuenta_bancaria": str(self.cuenta_bancaria),
            "turno_id": self.turno.id,
            "turno": str(self.turno),
            "concepto_id": self.concepto.id,
            "concepto": str(self.concepto),
            "archivo": self.archivo.url if self.archivo else None,
            "tipo_operacion": "gasto"
        })
        return data

