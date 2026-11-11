from django import forms
from .models import Producto


class ProductoForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        self.usuario = kwargs.pop("usuario")
        super().__init__(*args, **kwargs)

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

    def clean_nombre(self):
        nombre = self.cleaned_data["nombre"]

        existe = Producto.objects.filter(
            usuario=self.usuario,
            nombre__iexact=nombre
        ).exists()

        if existe:
            raise forms.ValidationError(
                "Ya tienes un producto con ese nombre."
            )

        return nombre