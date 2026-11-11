from django.shortcuts import render, redirect, get_object_or_404

from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import (
    UserCreationForm,
    AuthenticationForm
)

from .models import Producto
from .forms import ProductoForm


# REGISTRO
def registro(request):

    if request.method == "POST":
        form = UserCreationForm(request.POST)

        if form.is_valid():
            usuario = form.save()
            login(request, usuario)
            return redirect("inicio")

    else:
        form = UserCreationForm()

    return render(request, "inventario/registro.html", {
        "form": form
    })


# INICIO DE SESION
def iniciar_sesion(request):

    if request.method == "POST":
        form = AuthenticationForm(
            request,
            data=request.POST
        )

        if form.is_valid():
            usuario = form.get_user()
            login(request, usuario)
            return redirect("inicio")

    else:
        form = AuthenticationForm()

    return render(request, "inventario/login.html", {
        "form": form
    })


# CERRAR SESION
@login_required
def cerrar_sesion(request):

    if request.method == "POST":
        logout(request)

    return redirect("login")


# INVENTARIO
@login_required
def inicio(request):

    if request.method == "POST":
        form = ProductoForm(
            request.POST,
            usuario=request.user
        )

        if form.is_valid():
            producto = form.save(commit=False)
            producto.usuario = request.user
            producto.save()

            return redirect("inicio")

    else:
        form = ProductoForm(usuario=request.user)

    productos = Producto.objects.filter(
        usuario=request.user
    )

    return render(request, "inventario/inicio.html", {
        "form": form,
        "productos": productos
    })


# ELIMINAR PRODUCTO
@login_required
def eliminar_producto(request, producto_id):

    if request.method == "POST":
        producto = get_object_or_404(
            Producto,
            id=producto_id,
            usuario=request.user
        )

        producto.delete()

    return redirect("inicio")