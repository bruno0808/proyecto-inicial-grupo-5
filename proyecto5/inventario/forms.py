from django import forms
from .models import Compra, Producto


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
        ]

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


class CompraForm(forms.ModelForm):
    cantidad = forms.IntegerField(
        min_value=1,
        error_messages={
            "min_value": "La cantidad debe ser mayor que cero."
        },
        widget=forms.NumberInput(attrs={"min": 1})
    )

    class Meta:
        model = Compra
        fields = ["cantidad"]


class ConsumoForm(forms.Form):
    cantidad = forms.IntegerField(
        min_value=1,
        error_messages={
            "min_value": "La cantidad debe ser mayor que cero."
        },
        widget=forms.NumberInput(attrs={"min": 1})
    )

    def __init__(self, *args, **kwargs):
        self.producto = kwargs.pop("producto")
        super().__init__(*args, **kwargs)

    def clean_cantidad(self):
        cantidad = self.cleaned_data["cantidad"]
        if cantidad > self.producto.stock:
            raise forms.ValidationError(
                "No puedes quitar más unidades que las disponibles."
            )
        return cantidad