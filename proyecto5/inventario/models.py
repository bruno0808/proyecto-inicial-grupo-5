
from datetime import time
import math

from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class Producto(models.Model):\

    usuario = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="productos"
    )

    nombre = models.CharField(max_length=100)
    stock = models.PositiveIntegerField()
    consumo_diario = models.FloatField()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["usuario", "nombre"],
                name="producto_unico_por_usuario"
            )
        ]

    def dias_restantes(self):
        consumo_diario = self.consumo_diario_promedio()
        if consumo_diario <= 0:
            return None

        return self.stock / consumo_diario

    def consumo_diario_promedio(self):
        ventas = getattr(self, "historial_ventas", None)
        if ventas is None:
            ventas = list(self.ventas.all())

        if not ventas:
            return self.consumo_diario

        unidades_vendidas = sum(venta.cantidad for venta in ventas)
        primera_venta = min(
            venta.fecha_venta for venta in ventas
        )
        dias_transcurridos = max(
            (timezone.localdate() - primera_venta).days + 1,
            1
        )
        return unidades_vendidas / dias_transcurridos

    @property
    def hora_promedio_compra(self):
        ventas = getattr(self, "historial_ventas", None)
        if ventas is None:
            ventas = list(self.ventas.all())

        if not ventas:
            return None

        angulos = []
        for venta in ventas:
            if venta.hora_venta is None:
                continue
            minutos_del_dia = venta.hora_venta.hour * 60 + venta.hora_venta.minute
            angulos.append(2 * math.pi * minutos_del_dia / 1440)
        if not angulos:
            return None

        seno = sum(math.sin(angulo) for angulo in angulos)
        coseno = sum(math.cos(angulo) for angulo in angulos)

        if math.isclose(seno, 0, abs_tol=1e-12) and math.isclose(
            coseno, 0, abs_tol=1e-12
        ):
            return None

        minutos = round(
            (math.atan2(seno, coseno) % (2 * math.pi)) * 1440 / (2 * math.pi)
        ) % 1440
        return time(minutos // 60, minutos % 60)

    def cerca_de_agotarse(self):
        dias = self.dias_restantes()
        return dias is not None and dias <= 3

    def __str__(self):
        return self.nombre


class Compra(models.Model):
    producto = models.ForeignKey(
        Producto,
        on_delete=models.CASCADE,
        related_name="compras"
    )
    cantidad = models.IntegerField()
    fecha_compra = models.DateField(default=timezone.localdate)

    class Meta:
        ordering = ["-fecha_compra", "-id"]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(cantidad__gt=0),
                name="compra_cantidad_positiva"
            )
        ]

    def __str__(self):
        return f"{self.producto.nombre}: {self.cantidad} ({self.fecha_compra})"


class Venta(models.Model):
    producto = models.ForeignKey(
        Producto,
        on_delete=models.CASCADE,
        related_name="ventas"
    )
    cantidad = models.IntegerField()
    fecha_venta = models.DateField(default=timezone.localdate)
    hora_venta = models.TimeField(null=True, blank=True)

    class Meta:
        ordering = ["-fecha_venta", "-id"]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(cantidad__gt=0),
                name="venta_cantidad_positiva"
            )
        ]

    def __str__(self):
        return f"{self.producto.nombre}: {self.cantidad} ({self.fecha_venta})"