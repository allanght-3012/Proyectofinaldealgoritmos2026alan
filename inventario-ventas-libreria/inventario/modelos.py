"""Entidades del dominio: Producto y Venta."""
from __future__ import annotations
from dataclasses import dataclass
from datetime import date

from .excepciones import (
    CodigoInvalidoError,
    DatoInvalidoError,
    StockInsuficienteError,
)


class Producto:
    """Producto del inventario.

    Sus atributos son protegidos y solo se modifican mediante propiedades
    con validación o métodos como ``descontar_stock``.
    """

    LONGITUD_CODIGO: int = 7

    def __init__(self, codigo: str, nombre: str, categoria: str,
                 precio: float, stock: int) -> None:
        """Crea un producto validando cada dato.

        Args:
            codigo: código con formato LLL-DDD.
            nombre: nombre del producto (no vacío).
            categoria: categoría (no vacía).
            precio: precio unitario (>= 0).
            stock: unidades disponibles (entero >= 0).

        Raises:
            CodigoInvalidoError: si el código no cumple el formato.
            DatoInvalidoError: si nombre, categoría, precio o stock no son válidos.
        """
        self._codigo: str = ""
        self._nombre: str = ""
        self._categoria: str = ""
        self._precio: float = 0.0
        self._stock: int = 0
        self.codigo = codigo
        self.nombre = nombre
        self.categoria = categoria
        self.precio = precio
        self.stock = stock

    @staticmethod
    def normalizar_texto(texto: str) -> str:
        """Quita espacios extra y deja solo la primera letra en mayúscula.

        Args:
            texto: texto escrito por el usuario.

        Returns:
            Texto normalizado, p. ej. '  el   PRINCIPITO ' -> 'El principito'.
        """
        return " ".join(texto.split()).capitalize()

    @staticmethod
    def normalizar_codigo(codigo: str) -> str:
        """Quita espacios y pasa el código a mayúsculas.

        Args:
            codigo: código escrito por el usuario.

        Returns:
            Código normalizado, p. ej. ' lib-001 ' -> 'LIB-001'.
        """
        return codigo.strip().upper()

    @staticmethod
    def validar_codigo(codigo: str) -> bool:
        """Verifica el formato LLL-DDD (3 letras, guion, 3 dígitos).

        Args:
            codigo: código ya normalizado.

        Returns:
            True si el formato es válido, False en caso contrario.
        """
        return (len(codigo) == Producto.LONGITUD_CODIGO
                and codigo[:3].isalpha()
                and codigo[3] == "-"
                and codigo[4:].isdigit())

    @classmethod
    def desde_fila_csv(cls, fila: dict[str, str]) -> "Producto":
        """Construye un producto a partir de una fila leída del CSV.

        Args:
            fila: diccionario con las claves codigo, nombre, categoria,
                precio y stock (todas como texto).

        Returns:
            El Producto creado.

        Raises:
            CodigoInvalidoError: si el código no cumple el formato.
            DatoInvalidoError: si falta una columna o un dato no es válido.
        """
        try:
            return cls(fila["codigo"], fila["nombre"], fila["categoria"],
                       float(fila["precio"].replace(",", ".")),
                       int(fila["stock"]))
        except (KeyError, ValueError, AttributeError, TypeError) as error:
            raise DatoInvalidoError(
                f"Fila con datos incompletos o inválidos ({error})"
            ) from error

    @property
    def codigo(self) -> str:
        """Código del producto (formato LLL-DDD)."""
        return self._codigo

    @codigo.setter
    def codigo(self, valor: str) -> None:
        """Asigna el código normalizado.

        Raises:
            CodigoInvalidoError: si no cumple el formato LLL-DDD.
        """
        normalizado = self.normalizar_codigo(valor)
        if not self.validar_codigo(normalizado):
            raise CodigoInvalidoError(normalizado)
        self._codigo = normalizado

    @property
    def nombre(self) -> str:
        """Nombre del producto."""
        return self._nombre

    @nombre.setter
    def nombre(self, valor: str) -> None:
        """Asigna el nombre normalizado.

        Raises:
            DatoInvalidoError: si el nombre queda vacío.
        """
        normalizado = self.normalizar_texto(valor)
        if not normalizado:
            raise DatoInvalidoError("El nombre no puede estar vacío.")
        self._nombre = normalizado

    @property
    def categoria(self) -> str:
        """Categoría del producto (en minúsculas)."""
        return self._categoria

    @categoria.setter
    def categoria(self, valor: str) -> None:
        """Asigna la categoría en minúsculas.

        Raises:
            DatoInvalidoError: si la categoría queda vacía.
        """
        normalizada = " ".join(valor.split()).lower()
        if not normalizada:
            raise DatoInvalidoError("La categoría no puede estar vacía.")
        self._categoria = normalizada

    @property
    def precio(self) -> float:
        """Precio unitario del producto."""
        return self._precio

    @precio.setter
    def precio(self, valor: float) -> None:
        """Asigna el precio.

        Raises:
            DatoInvalidoError: si no es un número o es negativo.
        """
        try:
            numero = float(valor)
        except (TypeError, ValueError) as error:
            raise DatoInvalidoError("El precio debe ser un número.") from error
        if numero < 0:
            raise DatoInvalidoError("El precio no puede ser negativo.")
        self._precio = numero

    @property
    def stock(self) -> int:
        """Unidades disponibles."""
        return self._stock

    @stock.setter
    def stock(self, valor: int) -> None:
        """Asigna el stock.

        Raises:
            DatoInvalidoError: si no es un entero o es negativo.
        """
        try:
            entero = int(valor)
            es_entero = entero == float(valor)
        except (TypeError, ValueError) as error:
            raise DatoInvalidoError("El stock debe ser un número entero.") from error
        if not es_entero:
            raise DatoInvalidoError("El stock debe ser un número entero.")
        if entero < 0:
            raise DatoInvalidoError("El stock no puede ser negativo.")
        self._stock = entero

    def calcular_subtotal(self, cantidad: int) -> float:
        """Calcula el precio de varias unidades sin descuento.

        Args:
            cantidad: unidades a comprar.

        Returns:
            precio unitario por cantidad.
        """
        return self._precio * cantidad

    def descontar_stock(self, cantidad: int) -> None:
        """Resta unidades del stock.

        Args:
            cantidad: unidades vendidas (mayor que cero).

        Raises:
            DatoInvalidoError: si la cantidad es menor o igual a cero.
            StockInsuficienteError: si hay menos unidades que las pedidas.
        """
        if cantidad <= 0:
            raise DatoInvalidoError("La cantidad debe ser mayor que cero.")
        if cantidad > self._stock:
            raise StockInsuficienteError(self._nombre, self._stock)
        self._stock -= cantidad

    def a_fila_csv(self) -> list[str]:
        """Convierte el producto en una fila para guardar en el CSV.

        Returns:
            Lista [codigo, nombre, categoria, precio, stock].
        """
        return [self._codigo, self._nombre, self._categoria,
                f"{self._precio:.2f}", str(self._stock)]

    def __str__(self) -> str:
        """Texto legible del producto."""
        return (f"{self._codigo} - {self._nombre} "
                f"(${self._precio:.2f}, stock {self._stock})")

    def __repr__(self) -> str:
        """Representación técnica del producto."""
        return (f"Producto(codigo={self._codigo!r}, nombre={self._nombre!r}, "
                f"categoria={self._categoria!r}, precio={self._precio!r}, "
                f"stock={self._stock!r})")


@dataclass(frozen=True, repr=False)
class Venta:
    """Registro inmutable de una venta.

    Al ser ``frozen`` no se puede modificar después de creada. Referencia
    al objeto Producto que se vendió.
    """

    fecha: str
    producto: Producto
    cantidad: int
    descuento: float
    total: float

    @property
    def codigo_producto(self) -> str:
        """Código del producto vendido."""
        return self.producto.codigo

    @classmethod
    def nueva(cls, producto: Producto, cantidad: int,
              descuento: float, total: float) -> "Venta":
        """Crea una venta con la fecha de hoy.

        Args:
            producto: producto vendido.
            cantidad: unidades vendidas.
            descuento: porcentaje aplicado (0.10 = 10%).
            total: total cobrado.

        Returns:
            La Venta creada.
        """
        return cls(date.today().isoformat(), producto, cantidad,
                   descuento, total)

    @classmethod
    def desde_fila_csv(cls, fila: list[str], producto: Producto) -> "Venta":
        """Construye una venta a partir de una fila del archivo de ventas.

        Args:
            fila: lista [fecha, codigo, cantidad, descuento, total].
            producto: producto vendido (lo busca el repositorio por código).

        Returns:
            La Venta creada.

        Raises:
            DatoInvalidoError: si la fila está incompleta o tiene datos inválidos.
        """
        try:
            return cls(fila[0], producto, int(fila[2]), float(fila[3]),
                       float(fila[4]))
        except (IndexError, ValueError) as error:
            raise DatoInvalidoError(f"Venta con formato inválido: {fila}") from error

    def a_fila_csv(self) -> list[str]:
        """Convierte la venta en una fila para guardar en el CSV.

        Returns:
            Lista [fecha, codigo, cantidad, descuento, total].
        """
        return [self.fecha, self.producto.codigo, str(self.cantidad),
                str(self.descuento), f"{self.total:.2f}"]

    def __str__(self) -> str:
        """Texto legible de la venta."""
        return (f"{self.fecha}: {self.cantidad} x {self.producto.nombre} "
                f"(desc. {self.descuento:.0%}) = ${self.total:,.2f}")

    def __repr__(self) -> str:
        """Representación técnica de la venta."""
        return (f"Venta(fecha={self.fecha!r}, producto={self.producto.codigo!r}, "
                f"cantidad={self.cantidad!r}, descuento={self.descuento!r}, "
                f"total={self.total!r})")
