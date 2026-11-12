from django.db import transaction
from django.db.models import F, Prefetch
from django.shortcuts import render, redirect, get_object_or_404

from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import (
    UserCreationForm,
    AuthenticationForm
)

from .models import Compra, Producto
from .forms import CompraForm, ProductoForm


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

    return render_inicio(request, form)


def render_inicio(
    request,
    producto_form,
    compra_form=None,
    compra_producto_id=None
):
    productos = Producto.objects.filter(
        usuario=request.user
    ).prefetch_related(
        Prefetch(
            "compras",
            queryset=Compra.objects.order_by("-fecha_compra", "-id"),
            to_attr="historial_compras"
        )
    )

    for producto in productos:
        if producto.id == compra_producto_id:
            producto.compra_form = compra_form
        else:
            producto.compra_form = CompraForm()

    return render(request, "inventario/inicio.html", {
        "form": producto_form,
        "productos": productos
    })


# REGISTRAR COMPRA
@login_required
def registrar_compra(request, producto_id):
    if request.method != "POST":
        return redirect("inicio")

    producto = get_object_or_404(
        Producto,
        id=producto_id,
        usuario=request.user
    )
    form = CompraForm(request.POST)

    if form.is_valid():
        with transaction.atomic():
            compra = form.save(commit=False)
            compra.producto = producto
            compra.save()
            Producto.objects.filter(
                id=producto.id,
                usuario=request.user
            ).update(stock=F("stock") + compra.cantidad)

        return redirect("inicio")

    return render_inicio(
        request,
        ProductoForm(usuario=request.user),
        compra_form=form,
        compra_producto_id=producto.id
    )


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