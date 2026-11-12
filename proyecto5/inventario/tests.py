from django.http import Http404, HttpResponse
from django.contrib.auth.models import User
from django.test import RequestFactory, TestCase
from django.urls import reverse
from unittest.mock import patch
from .models import Compra, Producto
from .views import registrar_compra


class RegistrarCompraTests(TestCase):
    def setUp(self):
        self.usuario = User.objects.create_user(
            username="cliente",
            password="contrasena-segura"
        )
        self.producto = Producto.objects.create(
            usuario=self.usuario,
            nombre="Arroz",
            stock=10,
            consumo_diario=1,
            frecuencia_compra=7,
            hora_promedio_compra="09:00"
        )
        self.client.force_login(self.usuario)

    def test_compra_registra_cantidad_fecha_y_aumenta_stock(self):
        response = self.client.post(
            reverse("registrar_compra", args=[self.producto.id]),
            {"cantidad": 5}
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response["Location"], reverse("inicio"))
        self.producto.refresh_from_db()
        compra = Compra.objects.get(producto=self.producto)

        self.assertEqual(self.producto.stock, 15)
        self.assertEqual(compra.cantidad, 5)
        self.assertIsNotNone(compra.fecha_compra)

    def test_cantidad_cero_no_registra_compra_ni_cambia_stock(self):
        with patch(
            "inventario.views.render_inicio",
            return_value=HttpResponse()
        ) as render_inicio:
            response = self.client.post(
                reverse("registrar_compra", args=[self.producto.id]),
                {"cantidad": 0}
            )

        self.assertEqual(response.status_code, 200)
        compra_form = render_inicio.call_args.kwargs["compra_form"]
        self.assertFalse(compra_form.is_valid())
        self.producto.refresh_from_db()

        self.assertEqual(self.producto.stock, 10)
        self.assertFalse(Compra.objects.filter(producto=self.producto).exists())

    def test_usuario_no_puede_registrar_compra_a_producto_ajeno(self):
        otro_usuario = User.objects.create_user(
            username="otro",
            password="contrasena-segura"
        )
        request = RequestFactory().post(
            reverse("registrar_compra", args=[self.producto.id]),
            {"cantidad": 5}
        )
        request.user = otro_usuario

        with self.assertRaises(Http404):
            registrar_compra(request, self.producto.id)

        self.assertFalse(Compra.objects.filter(producto=self.producto).exists())
