from django.urls import path
from . import views

urlpatterns = [
    path("", views.inicio, name="inicio"),

    path("registro/", views.registro, name="registro"),

    path("login/", views.iniciar_sesion, name="login"),

    path("logout/", views.cerrar_sesion, name="logout"),

    path(
        "eliminar/<int:producto_id>/",
        views.eliminar_producto,
        name="eliminar_producto"
    ),
]