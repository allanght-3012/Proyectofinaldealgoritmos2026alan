"""Colección de productos del inventario."""
from __future__ import annotations
from typing import Iterator

from .excepciones import (
    DatoInvalidoError,
    ProductoDuplicadoError,
    ProductoNoEncontradoError,
)
from .modelos import Producto, Venta
from .reglas import ReglaNegocio


class Inventario:
    """Colección de objetos Producto indexados por código.

    Se encarga de agregar, eliminar, buscar, ordenar y vender productos.
    No lee ni escribe archivos ni imprime nada.
    """

    CRITERIOS_ORDEN: tuple = ("nombre", "precio", "stock", "categoria")

    def __init__(self) -> None:
        """Crea un inventario vacío."""
        self._productos: dict[str, Producto] = {}

    def agregar(self, producto: Producto) -> None:
        """Agrega un producto al inventario.

        Args:
            producto: producto a agregar.

        Raises:
            ProductoDuplicadoError: si ya existe un producto con ese código.
        """
        if producto.codigo in self._productos:
            raise ProductoDuplicadoError(producto.codigo)
        self._productos[producto.codigo] = producto

    def eliminar(self, codigo: str) -> Producto:
        """Quita un producto del inventario.

        Args:
            codigo: código del producto.

        Returns:
            El producto eliminado.

        Raises:
            ProductoNoEncontradoError: si el código no existe.
        """
        producto = self.obtener(codigo)
        del self._productos[producto.codigo]
        return producto

    def obtener(self, codigo: str) -> Producto:
        """Devuelve el producto con ese código.

        Args:
            codigo: código del producto (se normaliza).

        Returns:
            El Producto encontrado.

        Raises:
            ProductoNoEncontradoError: si el código no existe.
        """
        normalizado = Producto.normalizar_codigo(codigo)
        if normalizado not in self._productos:
            raise ProductoNoEncontradoError(normalizado)
        return self._productos[normalizado]

    def buscar(self, texto: str) -> list[Producto]:
        """Busca por código exacto o por coincidencia parcial.

        La coincidencia parcial se hace sobre el nombre y el código, sin
        distinguir mayúsculas de minúsculas.

        Args:
            texto: código o parte del nombre.

        Returns:
            Lista de productos que coinciden (vacía si no hay ninguno).
        """
        codigo = Producto.normalizar_codigo(texto)
        if codigo in self._productos:
            return [self._productos[codigo]]
        busqueda = " ".join(texto.split()).lower()
        return [p for p in self._productos.values()
                if busqueda in p.nombre.lower() or busqueda in p.codigo.lower()]

    def ordenar(self, criterio: str) -> list[Producto]:
        """Devuelve los productos ordenados por un criterio.

        Args:
            criterio: 'nombre', 'precio', 'stock' o 'categoria'.

        Returns:
            Lista de productos ordenada.

        Raises:
            DatoInvalidoError: si el criterio no es válido.
        """
        if criterio not in self.CRITERIOS_ORDEN:
            raise DatoInvalidoError("Criterio de ordenamiento no válido.")
        return sorted(self._productos.values(),
                      key=lambda producto: getattr(producto, criterio))

    def categorias(self) -> set[str]:
        """Devuelve las categorías existentes, sin duplicados.

        Returns:
            Conjunto (set) de categorías.
        """
        return {producto.categoria for producto in self._productos.values()}

    def vender(self, codigo: str, cantidad: int, regla: ReglaNegocio) -> Venta:
        """Registra una venta: descuenta stock y aplica la regla de descuento.

        Args:
            codigo: código del producto.
            cantidad: unidades a vender.
            regla: regla de descuento a aplicar (cualquier subclase).

        Returns:
            La Venta registrada (inmutable).

        Raises:
            ProductoNoEncontradoError: si el código no existe.
            DatoInvalidoError: si la cantidad es menor o igual a cero.
            StockInsuficienteError: si no hay unidades suficientes.
        """
        producto = self.obtener(codigo)
        producto.descontar_stock(cantidad)
        subtotal = producto.calcular_subtotal(cantidad)
        porcentaje, total = regla.aplicar(subtotal, cantidad)
        return Venta.nueva(producto, cantidad, porcentaje, total)

    def __len__(self) -> int:
        """Cantidad de productos: ``len(inventario)``."""
        return len(self._productos)

    def __contains__(self, codigo: object) -> bool:
        """Permite ``"LIB-001" in inventario`` (el código se normaliza)."""
        try:
            return Producto.normalizar_codigo(codigo) in self._productos
        except AttributeError:
            return False

    def __iter__(self) -> Iterator[Producto]:
        """Permite recorrer los productos con ``for p in inventario``."""
        return iter(self._productos.values())
