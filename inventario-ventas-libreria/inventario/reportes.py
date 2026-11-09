"""Formato de reportes en texto con columnas alineadas."""
from __future__ import annotations
from datetime import date
from typing import Iterable

from .modelos import Producto, Venta


class ReporteInventario:
    """Convierte una lista de productos en una tabla de texto alineada."""

    ANCHO_LINEA: int = 76

    def generar(self, productos: Iterable[Producto]) -> str:
        """Genera la tabla de productos.

        Args:
            productos: productos a mostrar.

        Returns:
            Texto con encabezado y una fila por producto.
        """
        filas = [f"{'Código':<10}{'Nombre':<36}{'Categoría':<14}{'Precio':>9}{'Stock':>7}",
                 "-" * self.ANCHO_LINEA]
        for p in productos:
            filas.append(f"{p.codigo:<10}{p.nombre[:34]:<36}{p.categoria:<14}"
                         f"{p.precio:>9.2f}{p.stock:>7}")
        return "\n".join(filas)


class ReporteVentas:
    """Genera el reporte de ventas del día con columnas alineadas."""

    ANCHO_LINEA: int = 76

    def generar(self, ventas: Iterable[Venta], fecha: str | None = None) -> str:
        """Genera el reporte de una fecha.

        Args:
            ventas: todas las ventas registradas.
            fecha: fecha ISO (AAAA-MM-DD); si es None se usa la de hoy.

        Returns:
            Texto del reporte con las ventas de esa fecha y su total.
        """
        dia = fecha or date.today().isoformat()
        del_dia = [v for v in ventas if v.fecha == dia]
        linea = "-" * self.ANCHO_LINEA
        texto = [f"REPORTE DE VENTAS - {dia}", linea,
                 f"{'Código':<10}{'Producto':<34}{'Cant.':>6}{'Desc.':>8}{'Total':>18}",
                 linea]
        suma = 0.0
        for venta in del_dia:
            texto.append(f"{venta.codigo_producto:<10}{venta.producto.nombre[:32]:<34}"
                         f"{venta.cantidad:>6}{venta.descuento:>8.0%}{venta.total:>18,.2f}")
            suma += venta.total
        if not del_dia:
            texto.append("No hay ventas registradas hoy.")
        texto += [linea, f"{'TOTAL DEL DÍA':<58}{suma:>18,.2f}"]
        return "\n".join(texto)
