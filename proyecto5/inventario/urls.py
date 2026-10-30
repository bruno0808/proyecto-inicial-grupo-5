from django.urls import path
from . import views

urlpatterns = [
    path("", views.inicio, name="inicio"),
     path(
        "eliminar/<int:producto_id>/",
        views.eliminar_producto,
        name="eliminar_producto"
    ),
]