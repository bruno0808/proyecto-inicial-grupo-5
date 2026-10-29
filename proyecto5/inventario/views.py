from django.shortcuts import render, redirect
from .models import Producto
from .forms import ProductoForm


def inicio(request):
    if request.method == "POST":
        form = ProductoForm(request.POST)

        if form.is_valid():
            form.save()
            return redirect("inicio")
    else:
        form = ProductoForm()

    productos = Producto.objects.all()

    return render(request, "inventario/inicio.html", {
        "form": form,
        "productos": productos,
    })