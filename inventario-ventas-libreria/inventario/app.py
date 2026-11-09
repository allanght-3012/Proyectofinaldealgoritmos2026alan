"""Interfaz de consola (Menu) y coordinación de los objetos (SistemaInventario)."""
from __future__ import annotations
from pathlib import Path

from .excepciones import (
    ArchivoDatosError,
    InventarioError,
    ProductoNoEncontradoError,
)
from .inventario import Inventario
from .modelos import Producto, Venta
from .persistencia import Bitacora, RepositorioCSV
from .reglas import DescuentoPorVolumen, ReglaNegocio, SinDescuento
from .reportes import ReporteInventario, ReporteVentas


class Menu:
    """Interfaz de consola: solo muestra textos y lee datos del usuario.

    No conoce productos, archivos ni reglas de negocio.
    """

    OPCIONES: tuple = (
        "1) Agregar producto",
        "2) Buscar producto",
        "3) Registrar venta",
        "4) Mostrar inventario",
        "5) Reporte de ventas del día",
        "6) Eliminar producto",
        "7) Cambiar regla de descuento",
        "8) Salir",
    )

    def mostrar_opciones(self) -> None:
        """Muestra el menú principal."""
        print("\n=== LIBRERÍA - INVENTARIO Y VENTAS (POO) ===")
        for opcion in self.OPCIONES:
            print(opcion)

    def pedir_texto(self, mensaje: str) -> str:
        """Pide un texto al usuario.

        Args:
            mensaje: texto que se muestra al pedir el dato.

        Returns:
            Lo que escribió el usuario, sin espacios en los extremos.
        """
        return input(mensaje).strip()

    def pedir_entero(self, mensaje: str) -> int:
        """Pide un entero y repite hasta que el usuario escriba uno válido.

        Args:
            mensaje: texto que se muestra al pedir el dato.

        Returns:
            El número entero escrito.
        """
        while True:
            try:
                return int(input(mensaje).strip())
            except ValueError:
                self.mostrar_error("Entrada inválida: escriba un número entero.")

    def pedir_decimal(self, mensaje: str) -> float:
        """Pide un decimal y repite hasta que el usuario escriba uno válido.

        Args:
            mensaje: texto que se muestra al pedir el dato.

        Returns:
            El número decimal escrito (acepta coma o punto).
        """
        while True:
            try:
                return float(input(mensaje).strip().replace(",", "."))
            except ValueError:
                self.mostrar_error("Entrada inválida: escriba un número (ej. 12.50).")

    def mostrar(self, mensaje: str) -> None:
        """Muestra un mensaje normal.

        Args:
            mensaje: texto a mostrar.
        """
        print(mensaje)

    def mostrar_error(self, mensaje: str) -> None:
        """Muestra un mensaje de error amigable.

        Args:
            mensaje: descripción del error.
        """
        print(f"Error: {mensaje}")


class SistemaInventario:
    """Coordina el menú, el inventario, el repositorio y la bitácora.

    Captura las excepciones del modelo y las muestra como mensajes, de modo
    que el programa no termina con un traceback.
    """

    CRITERIOS: dict = {"1": "nombre", "2": "precio", "3": "stock", "4": "categoria"}

    def __init__(self, ruta_inventario: str,
                 ruta_ventas: str | None = None,
                 ruta_bitacora: str | None = None) -> None:
        """Construye el sistema y sus colaboradores.

        Args:
            ruta_inventario: ruta del CSV del inventario (relativa a la raíz
                del proyecto o absoluta).
            ruta_ventas: ruta del CSV de ventas (por defecto junto al inventario).
            ruta_bitacora: ruta de la bitácora (por defecto junto al inventario).
        """
        raiz = Path(__file__).resolve().parents[1]
        ruta = Path(ruta_inventario)
        if not ruta.is_absolute():
            ruta = raiz / ruta
        self._menu: Menu = Menu()
        self._bitacora: Bitacora = Bitacora(Path(ruta_bitacora) if ruta_bitacora
                                            else ruta.parent / "bitacora.log")
        self._repositorio: RepositorioCSV = RepositorioCSV(
            ruta, Path(ruta_ventas) if ruta_ventas else ruta.parent / "ventas.csv",
            self._bitacora)
        self._inventario: Inventario = Inventario()
        self._ventas: list[Venta] = []
        self._regla_volumen: ReglaNegocio = DescuentoPorVolumen()
        self._regla_sin_descuento: ReglaNegocio = SinDescuento()
        self._regla: ReglaNegocio = self._regla_volumen
        self._activo: bool = True
        self._acciones: dict = {
            "1": self._agregar_producto,
            "2": self._buscar_producto,
            "3": self._registrar_venta,
            "4": self._mostrar_inventario,
            "5": self._reporte_ventas,
            "6": self._eliminar_producto,
            "7": self._cambiar_regla,
            "8": self._salir,
        }

    def ejecutar(self) -> None:
        """Carga los datos y ejecuta el menú hasta que el usuario elija salir."""
        try:
            self._inventario = self._repositorio.cargar_inventario()
            self._ventas = self._repositorio.cargar_ventas(self._inventario)
        except ArchivoDatosError as error:
            self._menu.mostrar_error(str(error))
            return
        for aviso in self._repositorio.avisos:
            self._menu.mostrar(f"AVISO: {aviso}")
        self._bitacora.registrar("Programa iniciado")
        while self._activo:
            self._menu.mostrar_opciones()
            opcion = self._menu.pedir_texto("Elija una opción: ")
            accion = self._acciones.get(opcion)
            if accion is None:
                self._menu.mostrar_error("Opción no válida.")
                continue
            try:
                accion()
            except InventarioError as error:
                self._menu.mostrar_error(str(error))

    def _agregar_producto(self) -> None:
        """Opción 1: pide los datos de un producto nuevo y lo agrega."""
        categorias = ", ".join(sorted(self._inventario.categorias()))
        self._menu.mostrar(f"Categorías existentes: {categorias}")
        codigo = self._menu.pedir_texto("Código (formato LLL-DDD): ")
        nombre = self._menu.pedir_texto("Nombre: ")
        categoria = self._menu.pedir_texto("Categoría: ")
        precio = self._menu.pedir_decimal("Precio: ")
        stock = self._menu.pedir_entero("Stock inicial: ")
        producto = Producto(codigo, nombre, categoria, precio, stock)
        self._inventario.agregar(producto)
        self._repositorio.guardar_inventario(self._inventario)
        self._bitacora.registrar(f"ALTA producto {producto.codigo} - {producto.nombre}")
        self._menu.mostrar("Producto agregado correctamente.")

    def _buscar_producto(self) -> None:
        """Opción 2: busca por código o parte del nombre y muestra el resultado.

        Raises:
            ProductoNoEncontradoError: si no hay coincidencias.
        """
        if len(self._inventario) == 0:
            self._menu.mostrar("El inventario está vacío. Revise datos/inventario.csv.")
            return
        texto = self._menu.pedir_texto("Código o parte del nombre: ")
        resultados = self._inventario.buscar(texto)
        if not resultados:
            codigos = ", ".join(p.codigo for p in self._inventario)
            self._menu.mostrar(f"Códigos disponibles: {codigos}")
            raise ProductoNoEncontradoError(texto)
        self._menu.mostrar(ReporteInventario().generar(resultados))

    def _registrar_venta(self) -> None:
        """Opción 3: pide código y cantidad y registra la venta."""
        codigo = self._menu.pedir_texto("Código del producto: ")
        producto = self._inventario.obtener(codigo)
        self._menu.mostrar(f"Producto: {producto.nombre} | Precio: ${producto.precio:.2f} "
                           f"| Stock: {producto.stock}")
        cantidad = self._menu.pedir_entero("Cantidad: ")
        venta = self._inventario.vender(codigo, cantidad, self._regla)
        self._ventas.append(venta)
        self._repositorio.guardar_venta(venta)
        self._repositorio.guardar_inventario(self._inventario)
        self._bitacora.registrar(f"VENTA {venta.codigo_producto} x{venta.cantidad} "
                                 f"desc={venta.descuento:.0%} total={venta.total:.2f}")
        self._menu.mostrar(f"Venta registrada: {venta.cantidad} x {producto.nombre} "
                           f"(descuento {venta.descuento:.0%}) -> Total: ${venta.total:,.2f}")

    def _mostrar_inventario(self) -> None:
        """Opción 4: muestra el inventario ordenado por el criterio elegido."""
        opcion = self._menu.pedir_texto(
            "Ordenar por: 1) Nombre  2) Precio  3) Stock  4) Categoría\nOpción: ")
        criterio = self.CRITERIOS.get(opcion, opcion)
        productos = self._inventario.ordenar(criterio)
        self._menu.mostrar(ReporteInventario().generar(productos))
        categorias = ", ".join(sorted(self._inventario.categorias()))
        self._menu.mostrar(f"Categorías: {categorias}")

    def _reporte_ventas(self) -> None:
        """Opción 5: muestra el reporte de ventas del día."""
        self._menu.mostrar(ReporteVentas().generar(self._ventas))

    def _eliminar_producto(self) -> None:
        """Opción 6: elimina un producto (baja)."""
        codigo = self._menu.pedir_texto("Código a eliminar: ")
        producto = self._inventario.eliminar(codigo)
        self._repositorio.guardar_inventario(self._inventario)
        self._bitacora.registrar(f"BAJA producto {producto.codigo} - {producto.nombre}")
        self._menu.mostrar(f"Producto eliminado: {producto.nombre}")

    def _cambiar_regla(self) -> None:
        """Opción 7: alterna entre descuento por volumen y sin descuento."""
        if self._regla is self._regla_volumen:
            self._regla = self._regla_sin_descuento
        else:
            self._regla = self._regla_volumen
        self._bitacora.registrar(f"Regla de descuento cambiada a: {self._regla}")
        self._menu.mostrar(f"Regla activa: {self._regla}")

    def _salir(self) -> None:
        """Opción 8: guarda los cambios y termina el programa."""
        self._repositorio.guardar_inventario(self._inventario)
        self._bitacora.registrar("Programa finalizado")
        self._menu.mostrar("Cambios guardados. ¡Hasta pronto!")
        self._activo = False
