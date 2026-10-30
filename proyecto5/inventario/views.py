from django.shortcuts import render, redirect, get_object_or_404
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

def eliminar_producto(request, producto_id):
    if request.method == "POST":
        producto = get_object_or_404(Producto, id=producto_id)
        producto.delete()

    return redirect("inicio")