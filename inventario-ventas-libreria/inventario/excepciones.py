"""Excepciones personalizadas del sistema de inventario y ventas."""
from __future__ import annotations


class InventarioError(Exception):
    """Excepción base de la que heredan todos los errores del sistema.

    Permite que la interfaz capture cualquier error propio con un solo
    ``except InventarioError``.
    """


class CodigoInvalidoError(InventarioError):
    """Se lanza cuando un código de producto no cumple el formato LLL-DDD."""

    def __init__(self, codigo: str) -> None:
        """Crea el error.

        Args:
            codigo: código que se intentó usar.
        """
        self.codigo: str = codigo
        super().__init__(
            f"Código '{codigo}' inválido: use el formato LLL-DDD (ej. LIB-013)."
        )


class DatoInvalidoError(InventarioError):
    """Se lanza cuando un dato no es válido (precio negativo, nombre vacío,
    cantidad menor o igual a cero, criterio de orden desconocido, etc.)."""


class ProductoDuplicadoError(InventarioError):
    """Se lanza al agregar un producto cuyo código ya existe."""

    def __init__(self, codigo: str) -> None:
        """Crea el error.

        Args:
            codigo: código repetido.
        """
        self.codigo: str = codigo
        super().__init__(f"El código {codigo} ya existe.")


class ProductoNoEncontradoError(InventarioError):
    """Se lanza cuando se busca un producto que no está en el inventario."""

    def __init__(self, codigo: str) -> None:
        """Crea el error.

        Args:
            codigo: código o texto que no produjo resultados.
        """
        self.codigo: str = codigo
        super().__init__(f"Producto '{codigo}' no encontrado.")


class StockInsuficienteError(InventarioError):
    """Se lanza cuando se pide más unidades de las que hay en stock."""

    def __init__(self, nombre: str, disponible: int) -> None:
        """Crea el error.

        Args:
            nombre: nombre del producto.
            disponible: unidades que hay realmente en stock.
        """
        self.disponible: int = disponible
        super().__init__(
            f"Stock insuficiente: solo hay {disponible} unidades de {nombre}."
        )


class ArchivoDatosError(InventarioError):
    """Se lanza cuando no se puede leer o escribir un archivo de datos."""
