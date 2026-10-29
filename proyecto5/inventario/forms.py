from django import forms
from .models import Producto


class ProductoForm(forms.ModelForm):
    class Meta:
        model = Producto
        fields = [
            "nombre",
            "stock",
            "consumo_diario",
            "frecuencia_compra",
            "hora_promedio_compra",
        ]

        widgets = {
            "hora_promedio_compra": forms.TimeInput(
                format="%H:%M",
                attrs={"type": "time"}
            )
        }