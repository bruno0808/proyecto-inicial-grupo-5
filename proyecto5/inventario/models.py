
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class Producto(models.Model):\

    usuario = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="productos"
    )

    nombre = models.CharField(max_length=100,unique=True)
    stock = models.PositiveIntegerField()
    consumo_diario = models.FloatField()
    frecuencia_compra = models.PositiveIntegerField(
        help_text="Cada cuántos días se compra normalmente"
    )
    hora_promedio_compra = models.TimeField()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["usuario", "nombre"],
                name="producto_unico_por_usuario"
            )
        ]

    def dias_restantes(self):
        if self.consumo_diario <= 0:
            return None

        return self.stock / self.consumo_diario

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
    cantidad = models.PositiveIntegerField()
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