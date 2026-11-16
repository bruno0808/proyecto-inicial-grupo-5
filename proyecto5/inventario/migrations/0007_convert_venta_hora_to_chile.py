from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from django.db import migrations


def convertir_horas_a_chile(apps, schema_editor):
    Venta = apps.get_model("inventario", "Venta")
    zona_chile = ZoneInfo("America/Santiago")
    ventas_actualizadas = []

    ventas = Venta.objects.exclude(hora_venta__isnull=True)
    for venta in ventas.iterator(chunk_size=200):
        fecha_hora_utc = datetime.combine(
            venta.fecha_venta,
            venta.hora_venta
        ).replace(tzinfo=timezone.utc)
        fecha_hora_chile = fecha_hora_utc.astimezone(zona_chile)
        venta.fecha_venta = fecha_hora_chile.date()
        venta.hora_venta = fecha_hora_chile.time().replace(tzinfo=None)
        ventas_actualizadas.append(venta)

        if len(ventas_actualizadas) == 200:
            Venta.objects.bulk_update(
                ventas_actualizadas,
                ["fecha_venta", "hora_venta"],
                batch_size=200
            )
            ventas_actualizadas.clear()

    if ventas_actualizadas:
        Venta.objects.bulk_update(
            ventas_actualizadas,
            ["fecha_venta", "hora_venta"],
            batch_size=200
        )


class Migration(migrations.Migration):

    dependencies = [
        ("inventario", "0006_remove_producto_hora_promedio_compra_and_more"),
    ]

    operations = [
        migrations.RunPython(convertir_horas_a_chile),
    ]
