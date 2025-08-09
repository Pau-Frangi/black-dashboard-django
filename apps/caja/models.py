from decimal import Decimal
from django.db import models
from apps.dyn_dt.models import UserTrackedModel, Turno, Concepto, Ejercicio, Campamento
from django.utils import timezone
from django.db.models.signals import post_save, pre_delete, post_delete
from django.dispatch import receiver
from django.core.exceptions import ValidationError
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey


class DenominacionEuro(UserTrackedModel, models.Model):
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




class Caja(UserTrackedModel, models.Model):
    """
    Representa una caja general
    """
    
    campamento = models.ForeignKey(
        Campamento,
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

    observaciones = models.TextField(
        blank=True,
        null=True,
        verbose_name="Observaciones"
    )

    def calcular_ingresos(self):
        """
        Calcula el importe total de MovimientosCajaIngreso asociados a esta caja.
        """
        ingresos = MovimientoCajaIngreso.objects.filter(caja=self)
        return sum(ingreso.importe for ingreso in ingresos) if ingresos else Decimal('0.00')
    
    def calcular_gastos(self):
        """
        Calcula el importe total de MovimientosCajaGasto asociados a esta caja.
        """
        gastos = MovimientoCajaGasto.objects.filter(caja=self)
        return sum(gasto.importe for gasto in gastos) if gastos else Decimal('0.00')
    
    def calcular_depositos(self):
        """
        Calcula el importe total de MovimientosCajaDeposito asociados a esta caja.
        """
        depositos = MovimientoCajaDeposito.objects.filter(caja=self)
        return sum(deposito.importe for deposito in depositos) if depositos else Decimal('0.00')

    def calcular_retiradas(self):
        """
        Calcula el importe total de MovimientosCajaRetirada asociados a esta caja.
        """
        retiradas = MovimientoCajaRetirada.objects.filter(caja=self)
        return sum(retirada.importe for retirada in retiradas) if retiradas else Decimal('0.00')
    
    def calcular_transferencias(self):
        """
        Calcula el importe total de MovimientosCajaTransferencia asociados a esta caja.
        Se tiene en cuenta que el efectivo sale de la caja original y entra en la caja destino.
        """
        total_transferencias_entrada = MovimientoCajaTransferencia.objects.filter(caja_destino=self)
        total_transferencias_salida = MovimientoCajaTransferencia.objects.filter(caja_origen=self)
        # Devolvemos un diccionario con las transferencias entrantes y salientes
        return {
            'entrada': sum(transferencia.importe for transferencia in total_transferencias_entrada) if total_transferencias_entrada else Decimal('0.00'),
            'salida': sum(transferencia.importe for transferencia in total_transferencias_salida) if total_transferencias_salida else Decimal('0.00')
        }

    def calcular_saldo_caja(self):
        """
        Calcula el saldo total de la caja.
        El saldo se calcula como:
        Saldo = Ingresos - Gastos + Depósitos - Retiradas + Transferencias Entrantes - Transferencias Salientes
        """
        ingresos = self.calcular_ingresos()
        gastos = self.calcular_gastos()
        depositos = self.calcular_depositos()
        retiradas = self.calcular_retiradas()
        transferencias = self.calcular_transferencias()

        saldo = (ingresos - gastos + depositos - retiradas +
                 transferencias['entrada'] - transferencias['salida'])
        
        return saldo if saldo >= 0 else Decimal('0.00')

    @property
    def saldo_caja(self):
        """
        Property to get the calculated saldo for serialization
        """
        return self.calcular_saldo_caja()

    def __str__(self):
        return f"{self.nombre} - {'Activa' if self.activa else 'Inactiva'} - Saldo: {self.calcular_saldo_caja():.2f}€"

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

    class Meta:
        verbose_name = "Caja"
        verbose_name_plural = "Cajas"
        ordering = ['-nombre']
        

class MovimientoCaja(UserTrackedModel, models.Model):
    """
    Modelo abstracto para movimientos económicos (de caja.
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

    class Meta:
        abstract = True

    def clean(self):
        """Validación de datos antes de guardar"""
        if self.importe <= 0:
            raise ValidationError("La cantidad debe ser positiva")
        
        if not self.caja.activa:
            raise ValidationError("No se pueden añadir movimientos a una caja inactiva")
        
    def serializar(self):
        return {
            "id": self.id,
            "importe": self.importe,
            "fecha": self.fecha,
            'fecha_completa': self.fecha.strftime('%Y-%m-%d %H:%M:%S'),
            'fecha_display': self.fecha.strftime('%d/%m/%Y %H:%M'),
            'datetime_iso': self.fecha.isoformat(),
            "descripcion": self.descripcion,
            "canal_movimiento": "caja"
        }
        
        
class MovimientoCajaIngreso(MovimientoCaja):
    """
    Modelo para registrar ingresos en la caja.
    """
    
    ejercicio = models.ForeignKey(
        Ejercicio,
        on_delete=models.CASCADE,
        verbose_name="Ejercicio",
        related_name="movimientos_caja_ingreso",
        help_text="Ejercicio contable al que pertenece este movimiento"
    )
    
    caja = models.ForeignKey(
        Caja,
        on_delete=models.CASCADE,
        verbose_name="Caja",
        related_name="movimientos_caja_ingreso",
        help_text="Caja donde se registra el movimiento de ingreso"
    )
    
    turno = models.ForeignKey(
        Turno,
        on_delete=models.CASCADE,
        verbose_name="Turno",
        related_name="movimientos_caja_ingreso",
        help_text="Turno al que pertenece este movimiento de ingreso"
    )
    
    concepto = models.ForeignKey(
        Concepto,
        on_delete=models.PROTECT,
        verbose_name="Concepto",
        related_name="movimientos_caja_ingreso",
        help_text="Concepto del movimiento de ingreso (ej. 'Inscripciones', 'Donación', etc.)"
    )
    
    archivo = models.FileField(
        upload_to='movimientos_ingreso/',
        null=True,
        blank=True,
        verbose_name="Archivo adjunto",
        help_text="Archivo relacionado con el movimiento de ingreso"
    )
    
    class Meta:
        verbose_name = "Movimiento de Ingreso"
        verbose_name_plural = "Movimientos de Ingreso"

    def __str__(self):
        return f"Ingreso de {self.importe} € en {self.caja} el {self.fecha}"
    
    def serializar(self):
        data = super().serializar()
        data.update({
            "ejercicio_id": self.ejercicio.id,
            "ejercicio": self.ejercicio.nombre,
            "caja_id": self.caja.id,
            "caja": self.caja.nombre,
            "turno_id": self.turno.id,
            "turno": self.turno.nombre,
            "concepto_id": self.concepto.id,
            "concepto": self.concepto.nombre,
            "archivo": self.archivo.url if self.archivo else None,
            "tipo_operacion": "ingreso"
        })
        return data
    
    
class MovimientoCajaGasto(MovimientoCaja):
    """
    Modelo para registrar gastos en la caja.
    """
    
    ejercicio = models.ForeignKey(
        Ejercicio,
        on_delete=models.CASCADE,
        verbose_name="Ejercicio",
        related_name="movimientos_caja_gasto",
        help_text="Ejercicio contable al que pertenece este movimiento"
    )
    
    caja = models.ForeignKey(
        Caja,
        on_delete=models.CASCADE,
        verbose_name="Caja",
        related_name="movimientos_caja_gasto",
        help_text="Caja donde se registra el movimiento de gasto"
    )
    
    turno = models.ForeignKey(
        Turno,
        on_delete=models.CASCADE,
        verbose_name="Turno",
        related_name="movimientos_caja_gasto",
        help_text="Turno al que pertenece este movimiento de gasto"
    )
    
    concepto = models.ForeignKey(
        Concepto,
        on_delete=models.PROTECT,
        verbose_name="Concepto",
        related_name="movimientos_caja_gasto",
        help_text="Concepto del movimiento de gasto (ej. 'Compra de comida', 'Materiales', etc.)"
    )
    
    archivo = models.FileField(
        upload_to='movimientos_gasto/',
        null=True,
        blank=True,
        verbose_name="Archivo adjunto",
        help_text="Archivo relacionado con el movimiento de gasto"
    )
    
    class Meta:
        verbose_name = "Movimiento de Gasto"
        verbose_name_plural = "Movimientos de Gasto"

    def __str__(self):
        return f"Gasto de {self.importe} € en {self.caja} el {self.fecha}"
    
    def serializar(self):
        data = super().serializar()
        data.update({
            "ejercicio_id": self.ejercicio.id,
            "ejercicio": self.ejercicio.nombre,
            "caja_id": self.caja.id,
            "caja": self.caja.nombre,
            "turno_id": self.turno.id,
            "turno": self.turno.nombre,
            "concepto_id": self.concepto.id,
            "concepto": self.concepto.nombre,
            "archivo": self.archivo.url if self.archivo else None,
            "tipo_operacion": "gasto"
        })
        return data
    
    
class MovimientoCajaTransferencia(MovimientoCaja):
    """
    Modelo para registrar transferencias entre cajas.
    """
    
    ejercicio = models.ForeignKey(
        Ejercicio,
        on_delete=models.CASCADE,
        verbose_name="Ejercicio",
        related_name="movimientos_caja_transferencia",
        help_text="Ejercicio contable al que pertenece este movimiento"
    )
    
    caja_origen = models.ForeignKey(
        Caja,
        on_delete=models.CASCADE,
        verbose_name="Caja de origen",
        related_name="movimientos_caja_transferencia_origen",
        help_text="Caja donde se registra el movimiento de transferencia"
    )
    
    caja_destino = models.ForeignKey(
        Caja,
        on_delete=models.CASCADE,
        verbose_name="Caja de destino",
        related_name="movimientos_caja_transferencia_destino",
    )    
    
    turno = models.ForeignKey(
        Turno,
        on_delete=models.CASCADE,
        verbose_name="Turno",
        related_name="movimientos_caja_transferencia",
        help_text="Turno al que pertenece este movimiento de transferencia"
    )
    
    class Meta:
        verbose_name = "Movimiento de Transferencia"
        verbose_name_plural = "Movimientos de Transferencia"
        
    def __str__(self):
        return f"Transferencia de {self.importe} € de {self.caja_origen} a {self.caja_destino} el {self.fecha}"
    
    def serializar(self):
        data = super().serializar()
        data.update({
            "ejercicio_id": self.ejercicio.id,
            "ejercicio": self.ejercicio.nombre,
            "caja_origen_id": self.caja_origen.id,
            "caja_origen": self.caja_origen.nombre,
            "caja_destino_id": self.caja_destino.id,
            "caja_destino": self.caja_destino.nombre,
            "turno_id": self.turno.id,
            "turno": self.turno.nombre,
            "tipo_operacion": "transferencia"
        })
        return data


class MovimientoCajaDeposito(MovimientoCaja):
    """
    Modelo para registrar depósitos en la caja.
    """
    
    ejercicio = models.ForeignKey(
        Ejercicio,
        on_delete=models.CASCADE,
        verbose_name="Ejercicio",
        related_name="movimientos_caja_deposito",
        help_text="Ejercicio contable al que pertenece este movimiento"
    )
    
    caja = models.ForeignKey(
        Caja,
        on_delete=models.CASCADE,
        verbose_name="Caja",
        related_name="movimientos_caja_deposito",
        help_text="Caja donde se registra el movimiento de depósito"
    )
    
    turno = models.ForeignKey(
        Turno,
        on_delete=models.CASCADE,
        verbose_name="Turno",
        related_name="movimientos_caja_deposito",
        help_text="Turno al que pertenece este movimiento de depósito"
    )
    
    def __str__(self):
        return f"Depósito de {self.importe} € en {self.caja} el {self.fecha}"
    
    class Meta:
        verbose_name = "Movimiento de Depósito"
        verbose_name_plural = "Movimientos de Depósito"
        
    def serializar(self):
        data = super().serializar()
        data.update({
            "ejercicio_id": self.ejercicio.id,
            "ejercicio": self.ejercicio.nombre,
            "caja_id": self.caja.id,
            "caja": self.caja.nombre,
            "turno_id": self.turno.id,
            "turno": self.turno.nombre,
            "tipo_operacion": "deposito"
        })
        return data
        
        
class MovimientoCajaRetirada(MovimientoCaja):
    """
    Modelo para registrar retiradas de efectivo de la caja.
    """

    ejercicio = models.ForeignKey(
        Ejercicio,
        on_delete=models.CASCADE,
        verbose_name="Ejercicio",
        related_name="movimientos_caja_retirada",
        help_text="Ejercicio contable al que pertenece este movimiento"
    )
    
    caja = models.ForeignKey(
        Caja,
        on_delete=models.CASCADE,
        verbose_name="Caja",
        related_name="movimientos_caja_retirada",
        help_text="Caja donde se registra el movimiento de retirada"
    )
    
    turno = models.ForeignKey(
        Turno,
        on_delete=models.CASCADE,
        verbose_name="Turno",
        related_name="movimientos_caja_retirada",
        help_text="Turno al que pertenece este movimiento de retirada"
    )

    retirado_por = models.CharField(
        max_length=100,
        verbose_name="Retirado por",
        help_text="Nombre de la persona que retira el efectivo"
    )
    
    def __str__(self):
        return f"Retirada de {self.importe} € de {self.caja} el {self.fecha}"
    
    class Meta:
        verbose_name = "Movimiento de Retirada"
        verbose_name_plural = "Movimientos de Retirada"
        
    def serializar(self):
        data = super().serializar()
        data.update({
            "ejercicio_id": self.ejercicio.id,
            "ejercicio": self.ejercicio.nombre,
            "caja_id": self.caja.id,
            "caja": self.caja.nombre,
            "turno_id": self.turno.id,
            "turno": self.turno.nombre,         
            "retirado_por": self.retirado_por,
            "tipo_operacion": "retirada"
        })
        return data
        
        
        
class DesgloseCaja(UserTrackedModel, models.Model):
    """
    Representa la cantidad de cada denominación en una caja específica
    """
    caja = models.ForeignKey(
        Caja,
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
         
        
class MovimientoEfectivo(UserTrackedModel, models.Model):
    """
    Representa el movimiento específico de denominaciones en un movimiento de caja
    """
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        verbose_name="Tipo de movimiento de caja"
    )
    
    object_id = models.PositiveIntegerField(
        verbose_name="ID del objeto"
    )
    
    movimiento_caja = GenericForeignKey('content_type', 'object_id')
    
    caja = models.ForeignKey(
        Caja,
        on_delete=models.CASCADE,
        verbose_name="Caja",
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
        """Calcula el numero de denominaciones neto (entrada - salida)"""
        return self.cantidad_entrada - self.cantidad_salida

    def importe_neto(self):
        """Calcula el importe neto del movimiento"""
        return self.importe_neto() * self.denominacion.valor

    def __str__(self):
        return f"{self.movimiento_caja} - {self.denominacion}: +{self.cantidad_entrada}/-{self.cantidad_salida}"

    def debug(self):
        print("Generic FK resolved as:", self.movimiento_caja)
        print("content_type:", self.content_type)
        print("object_id:", self.object_id)

    class Meta:
        verbose_name = "Movimiento de Efectivo"
        verbose_name_plural = "Movimientos de Efectivo"


################################################################
#   Señales para eliminar movimientos de efectivo relacionados   #
################################################################

@receiver(pre_delete, sender=MovimientoCajaIngreso)
def eliminar_movimientos_efectivo_relacionados(sender, instance, **kwargs):
    ct = ContentType.objects.get_for_model(instance)
    MovimientoEfectivo.objects.filter(content_type=ct, object_id=instance.id).delete()

@receiver(pre_delete, sender=MovimientoCajaGasto)
def eliminar_movimientos_efectivo_relacionados(sender, instance, **kwargs):
    ct = ContentType.objects.get_for_model(instance)
    MovimientoEfectivo.objects.filter(content_type=ct, object_id=instance.id).delete()
    
@receiver(pre_delete, sender=MovimientoCajaTransferencia)
def eliminar_movimientos_efectivo_relacionados(sender, instance, **kwargs):
    ct = ContentType.objects.get_for_model(instance)
    MovimientoEfectivo.objects.filter(content_type=ct, object_id=instance.id).delete()
    
@receiver(pre_delete, sender=MovimientoCajaDeposito)
def eliminar_movimientos_efectivo_relacionados(sender, instance, **kwargs):
    ct = ContentType.objects.get_for_model(instance)
    MovimientoEfectivo.objects.filter(content_type=ct, object_id=instance.id).delete()
    
@receiver(pre_delete, sender=MovimientoCajaRetirada)
def eliminar_movimientos_efectivo_relacionados(sender, instance, **kwargs):
    ct = ContentType.objects.get_for_model(instance)
    MovimientoEfectivo.objects.filter(content_type=ct, object_id=instance.id).delete()
    

#############################################################################
#   Señales para actualizar el desglose de la caja al crear un movimiento   #
#############################################################################


@receiver(post_save, sender=MovimientoEfectivo)
def actualizar_desglose_on_movimiento_efectivo_save(sender, instance, created, **kwargs):
    """Actualiza el desglose de la caja al crear o actualizar un MovimientoEfectivo"""
    if created:
        desglose_caja, created_desglose = DesgloseCaja.objects.get_or_create(
            caja=instance.caja,
            denominacion=instance.denominacion,
            defaults={'cantidad': 0, 'creado_por': instance.creado_por}
        )
        desglose_caja.cantidad += instance.cantidad_entrada - instance.cantidad_salida
        if desglose_caja.cantidad < 0:
            desglose_caja.cantidad = 0  
        desglose_caja.save()
        
        
@receiver(post_delete, sender=MovimientoEfectivo)
def actualizar_desglose_on_movimiento_dinero_delete(sender, instance, **kwargs):
    """Actualiza el desglose cuando se elimina un MovimientoDinero"""
    desglose = DesgloseCaja.objects.filter(
        caja=instance.caja,
        denominacion=instance.denominacion
    ).first()
    if desglose:
        desglose.cantidad -= instance.cantidad_neta()
        if desglose.cantidad < 0:
            desglose.cantidad = 0
        desglose.save()
        
        
##############################################################################
#   Señal para inicializar el desglose de la caja al crear una nueva caja    #
##############################################################################
        
@receiver(post_save, sender=Caja)
def inicializar_desglose_caja(sender, instance, created, **kwargs):
    """Inicializa el desglose cuando se crea una nueva caja"""
    if created:
        instance.inicializar_desglose()