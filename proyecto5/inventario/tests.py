from datetime import datetime, time, timedelta, timezone as datetime_timezone
from unittest.mock import patch

from django.http import Http404, HttpResponse
from django.contrib.auth.models import User
from django.test import RequestFactory, TestCase
from django.urls import reverse
from django.utils import timezone

from .forms import ProductoForm
from .models import Compra, Producto, Venta
from .views import registrar_compra, registrar_consumo, render_inicio


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
            consumo_diario=1
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

    def test_producto_muestra_nombre_stock_y_estado_al_cerrarse(self):
        response = self.client.get(reverse("inicio"))
        contenido = response.content.decode()

        self.assertRegex(
            contenido,
            r'<details class="producto"\s*>\s*<summary class="producto-resumen">'
        )
        self.assertContains(response, "Arroz")
        self.assertContains(response, "Stock: 10")
        self.assertContains(response, "Stock suficiente")

    def test_producto_sin_stock_muestra_agotado_aunque_no_haya_prediccion(self):
        self.producto.stock = 0
        self.producto.consumo_diario = 0
        self.producto.save(update_fields=["stock", "consumo_diario"])

        response = self.client.get(reverse("inicio"))
        contenido = response.content.decode()

        self.assertRegex(
            contenido,
            r'<span class="producto-estado estado-alerta">\s*Agotado\s*</span>'
        )
        self.assertContains(response, "¡Producto agotado!")
        self.assertNotContains(response, "Sin predicción")
        self.assertNotContains(response, "No se puede calcular la predicción.")

    def test_producto_se_abre_si_el_formulario_de_compra_tiene_errores(self):
        response = self.client.post(
            reverse("registrar_compra", args=[self.producto.id]),
            {"cantidad": 0}
        )

        self.assertRegex(
            response.content.decode(),
            r'<details class="producto"\s+open>'
        )

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

    def test_consumo_disminuye_stock(self):
        response = self.client.post(
            reverse("registrar_consumo", args=[self.producto.id]),
            {"cantidad": 4}
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response["Location"], reverse("inicio"))
        self.producto.refresh_from_db()
        venta = Venta.objects.get(producto=self.producto)
        self.assertEqual(self.producto.stock, 6)
        self.assertEqual(venta.cantidad, 4)
        self.assertIsNotNone(venta.fecha_venta)
        self.assertIsNotNone(venta.hora_venta)

    def test_consumo_registra_hora_en_zona_chilena(self):
        instante_utc = datetime(
            2026, 11, 15, 21, 0, tzinfo=datetime_timezone.utc
        )
        with patch(
            "inventario.views.timezone.now",
            return_value=instante_utc
        ):
            self.client.post(
                reverse("registrar_consumo", args=[self.producto.id]),
                {"cantidad": 1}
            )

        venta = Venta.objects.get(producto=self.producto)
        self.assertEqual(venta.fecha_venta, instante_utc.date())
        self.assertEqual(venta.hora_venta, time(18, 0))

    def test_prediccion_se_actualiza_con_el_historial_de_ventas(self):
        Venta.objects.create(
            producto=self.producto,
            cantidad=5,
            fecha_venta=timezone.localdate() - timedelta(days=4)
        )

        self.client.post(
            reverse("registrar_consumo", args=[self.producto.id]),
            {"cantidad": 2}
        )

        self.producto.refresh_from_db()
        self.assertAlmostEqual(self.producto.consumo_diario_promedio(), 1.4)
        self.assertAlmostEqual(self.producto.dias_restantes(), 8 / 1.4)

    def test_prediccion_usa_consumo_configurado_si_no_hay_ventas(self):
        self.assertEqual(self.producto.consumo_diario_promedio(), 1)
        self.assertEqual(self.producto.dias_restantes(), 10)

    def test_formulario_no_pide_hora_promedio_de_compra(self):
        form = ProductoForm(
            data={
                "nombre": "Frijoles",
                "stock": 5,
                "consumo_diario": 1
            },
            usuario=self.usuario
        )

        self.assertTrue(form.is_valid(), form.errors)
        self.assertNotIn("hora_promedio_compra", form.fields)
        self.assertNotIn("frecuencia_compra", form.fields)

    def test_hora_promedio_se_calcula_con_el_historial_de_ventas(self):
        ahora = timezone.localtime()
        Venta.objects.create(
            producto=self.producto,
            cantidad=1,
            fecha_venta=ahora.date(),
            hora_venta=ahora.replace(
                hour=9, minute=0, second=0, microsecond=0
            ).time()
        )
        Venta.objects.create(
            producto=self.producto,
            cantidad=1,
            fecha_venta=ahora.date(),
            hora_venta=ahora.replace(
                hour=11, minute=0, second=0, microsecond=0
            ).time()
        )

        self.assertEqual(self.producto.hora_promedio_compra, time(10, 0))

    def test_hora_promedio_considera_ventas_cercanas_a_medianoche(self):
        ahora = timezone.localtime()
        Venta.objects.create(
            producto=self.producto,
            cantidad=1,
            fecha_venta=ahora.date(),
            hora_venta=ahora.replace(
                hour=23, minute=0, second=0, microsecond=0
            ).time()
        )
        Venta.objects.create(
            producto=self.producto,
            cantidad=1,
            fecha_venta=ahora.date(),
            hora_venta=ahora.replace(
                hour=1, minute=0, second=0, microsecond=0
            ).time()
        )

        self.assertEqual(self.producto.hora_promedio_compra, time(0, 0))

    def test_hora_promedio_no_disponible_sin_ventas(self):
        self.assertIsNone(self.producto.hora_promedio_compra)

    def test_hora_promedio_ignora_ventas_historicas_sin_hora(self):
        Venta.objects.create(producto=self.producto, cantidad=1)

        self.assertIsNone(self.producto.hora_promedio_compra)

    def test_consumo_mayor_al_stock_no_lo_disminuye(self):
        with patch(
            "inventario.views.render_inicio",
            return_value=HttpResponse()
        ) as render_inicio:
            response = self.client.post(
                reverse("registrar_consumo", args=[self.producto.id]),
                {"cantidad": 11}
            )

        self.assertEqual(response.status_code, 200)
        consumo_form = render_inicio.call_args.kwargs["consumo_form"]
        self.assertFalse(consumo_form.is_valid())
        self.producto.refresh_from_db()
        self.assertEqual(self.producto.stock, 10)
        self.assertFalse(Venta.objects.filter(producto=self.producto).exists())

    def test_usuario_no_puede_quitar_stock_a_producto_ajeno(self):
        otro_usuario = User.objects.create_user(
            username="otro",
            password="contrasena-segura"
        )
        request = RequestFactory().post(
            reverse("registrar_consumo", args=[self.producto.id]),
            {"cantidad": 5}
        )
        request.user = otro_usuario

        with self.assertRaises(Http404):
            registrar_consumo(request, self.producto.id)

        self.producto.refresh_from_db()
        self.assertEqual(self.producto.stock, 10)

    def test_historial_compras_se_carga_para_mostrarlo(self):
        compra = Compra.objects.create(
            producto=self.producto,
            cantidad=3
        )
        request = RequestFactory().get(reverse("inicio"))
        request.user = self.usuario

        with patch("inventario.views.render", return_value=HttpResponse()) as render:
            render_inicio(request, ProductoForm(usuario=self.usuario))

        productos = list(render.call_args.args[2]["productos"])
        self.assertEqual(productos[0].historial_compras, [compra])

    def test_otro_usuario_puede_usar_el_mismo_nombre_de_producto(self):
        otro_usuario = User.objects.create_user(
            username="otro",
            password="contrasena-segura"
        )
        self.client.force_login(otro_usuario)

        response = self.client.post(
            reverse("inicio"),
            {
                "nombre": self.producto.nombre,
                "stock": 5,
                "consumo_diario": 1
            }
        )

        self.assertEqual(response.status_code, 302)
        self.assertTrue(
            Producto.objects.filter(
                usuario=otro_usuario,
                nombre=self.producto.nombre
            ).exists()
        )

    def test_mismo_usuario_no_puede_repetir_nombre_de_producto(self):
        form = ProductoForm(
            data={
                "nombre": "arroz",
                "stock": 5,
                "consumo_diario": 1
            },
            usuario=self.usuario
        )

        self.assertFalse(form.is_valid())
        self.assertIn("nombre", form.errors)
