
from django.db import models


class Producto(models.Model):
    nombre = models.CharField(max_length=100)
    stock = models.PositiveIntegerField()
    consumo_diario = models.FloatField()
    frecuencia_compra = models.PositiveIntegerField(
        help_text="Cada cuántos días se compra normalmente"
    )
    hora_promedio_compra = models.TimeField()

    def dias_restantes(self):
        if self.consumo_diario <= 0:
            return None

        return self.stock / self.consumo_diario

    def cerca_de_agotarse(self):
        dias = self.dias_restantes()
        return dias is not None and dias <= 3

    def __str__(self):
        return self.nombre