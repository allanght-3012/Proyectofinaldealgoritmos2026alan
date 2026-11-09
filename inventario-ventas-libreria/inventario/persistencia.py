"""Persistencia en archivos: bitácora y repositorio CSV."""
from __future__ import annotations
import csv
from datetime import datetime
from pathlib import Path

from .excepciones import ArchivoDatosError, InventarioError
from .inventario import Inventario
from .modelos import Producto, Venta


class Bitacora:
    """Registra operaciones con fecha y hora en un archivo, en modo append."""

    def __init__(self, ruta: Path) -> None:
        """Crea la bitácora.

        Args:
            ruta: ruta del archivo de bitácora.
        """
        self._ruta: Path = Path(ruta)

    def registrar(self, mensaje: str) -> bool:
        """Agrega una línea con fecha y hora al final del archivo.

        La bitácora nunca detiene el programa: si no puede escribir,
        devuelve False.

        Args:
            mensaje: descripción de la operación.

        Returns:
            True si se escribió, False si hubo un error de archivo.
        """
        marca = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        try:
            self._ruta.parent.mkdir(parents=True, exist_ok=True)
            with open(self._ruta, "a", encoding="utf-8") as archivo:
                archivo.write(f"[{marca}] {mensaje}\n")
            return True
        except OSError:
            return False


class RepositorioCSV:
    """Lee y escribe el inventario y las ventas en archivos CSV.

    No calcula descuentos ni imprime: solo mueve datos entre archivos y
    objetos. Los problemas no graves se guardan en ``avisos``.
    """

    ENCABEZADOS_INVENTARIO: tuple = ("codigo", "nombre", "categoria", "precio", "stock")
    ENCABEZADOS_VENTAS: tuple = ("fecha", "codigo", "cantidad", "descuento", "total")

    def __init__(self, ruta_inventario: Path, ruta_ventas: Path,
                 bitacora: Bitacora) -> None:
        """Crea el repositorio.

        Args:
            ruta_inventario: ruta del CSV del inventario.
            ruta_ventas: ruta del CSV de ventas.
            bitacora: bitácora donde se anotan las operaciones.
        """
        self._ruta_inventario: Path = Path(ruta_inventario)
        self._ruta_ventas: Path = Path(ruta_ventas)
        self._bitacora: Bitacora = bitacora
        self._avisos: list[str] = []

    @property
    def avisos(self) -> list[str]:
        """Avisos de la última carga (archivo creado, filas omitidas)."""
        return list(self._avisos)

    @staticmethod
    def _detectar_delimitador(archivo) -> str:
        """Detecta si el CSV usa coma o punto y coma (Excel en español).

        Args:
            archivo: archivo de texto abierto; se deja de nuevo al inicio.

        Returns:
            ';' o ','.
        """
        primera_linea = archivo.readline()
        archivo.seek(0)
        return ";" if primera_linea.count(";") > primera_linea.count(",") else ","

    def _crear_archivo(self, ruta: Path, encabezados: tuple) -> None:
        """Crea un archivo CSV nuevo que solo tiene los encabezados.

        Args:
            ruta: ruta del archivo.
            encabezados: nombres de las columnas.

        Raises:
            ArchivoDatosError: si no se puede crear el archivo.
        """
        try:
            ruta.parent.mkdir(parents=True, exist_ok=True)
            with open(ruta, "w", newline="", encoding="utf-8") as archivo:
                csv.writer(archivo).writerow(encabezados)
            self._bitacora.registrar(f"Archivo nuevo creado: {ruta.name}")
        except OSError as error:
            raise ArchivoDatosError(f"No se pudo crear {ruta.name}: {error}") from error

    def cargar_inventario(self) -> Inventario:
        """Carga el inventario desde el CSV.

        Si el archivo no existe lo crea con encabezados y devuelve un
        inventario vacío. Las filas inválidas se omiten y quedan en ``avisos``.

        Returns:
            Inventario con los productos cargados.

        Raises:
            ArchivoDatosError: si el archivo no se puede abrir o crear.
        """
        inventario = Inventario()
        self._avisos = []
        try:
            with open(self._ruta_inventario, newline="", encoding="utf-8-sig") as archivo:
                lector = csv.DictReader(archivo, delimiter=self._detectar_delimitador(archivo))
                if lector.fieldnames:
                    lector.fieldnames = [c.strip().lower() for c in lector.fieldnames]
                for numero, fila in enumerate(lector, start=2):
                    try:
                        inventario.agregar(Producto.desde_fila_csv(fila))
                    except InventarioError as error:
                        self._avisos.append(f"Fila {numero} omitida: {error}")
                        self._bitacora.registrar(f"Fila {numero} omitida al cargar: {error}")
        except FileNotFoundError:
            self._crear_archivo(self._ruta_inventario, self.ENCABEZADOS_INVENTARIO)
            self._avisos.append(
                "No existe el archivo de inventario; se creó uno nuevo con encabezados."
            )
        except OSError as error:
            raise ArchivoDatosError(f"No se pudo abrir el inventario: {error}") from error
        self._bitacora.registrar(f"Inventario cargado: {len(inventario)} productos")
        return inventario

    def guardar_inventario(self, inventario: Inventario) -> None:
        """Reescribe el CSV con el estado actual del inventario.

        Args:
            inventario: inventario a guardar.

        Raises:
            ArchivoDatosError: si no se puede escribir el archivo.
        """
        try:
            self._ruta_inventario.parent.mkdir(parents=True, exist_ok=True)
            with open(self._ruta_inventario, "w", newline="", encoding="utf-8") as archivo:
                escritor = csv.writer(archivo)
                escritor.writerow(self.ENCABEZADOS_INVENTARIO)
                for producto in inventario:
                    escritor.writerow(producto.a_fila_csv())
        except OSError as error:
            raise ArchivoDatosError(f"No se pudo guardar el inventario: {error}") from error
        self._bitacora.registrar(f"Inventario guardado: {len(inventario)} productos")

    def cargar_ventas(self, inventario: Inventario) -> list[Venta]:
        """Carga las ventas guardadas.

        Cada venta se enlaza con el objeto Producto del inventario. Si el
        archivo no existe lo crea con encabezados. Las filas inválidas, o de
        productos que ya no existen, se omiten y quedan en ``avisos``.

        Args:
            inventario: inventario ya cargado, para buscar cada producto.

        Returns:
            Lista de ventas (objetos Venta inmutables).

        Raises:
            ArchivoDatosError: si el archivo no se puede abrir o crear.
        """
        ventas: list[Venta] = []
        try:
            with open(self._ruta_ventas, newline="", encoding="utf-8-sig") as archivo:
                lector = csv.reader(archivo)
                next(lector, None)
                for fila in lector:
                    try:
                        producto = inventario.obtener(fila[1])
                        ventas.append(Venta.desde_fila_csv(fila, producto))
                    except IndexError:
                        self._avisos.append(f"Venta omitida: fila incompleta {fila}")
                        self._bitacora.registrar(f"Venta omitida al cargar: {fila}")
                    except InventarioError as error:
                        self._avisos.append(f"Venta omitida: {error}")
                        self._bitacora.registrar(f"Venta omitida al cargar: {error}")
        except FileNotFoundError:
            self._crear_archivo(self._ruta_ventas, self.ENCABEZADOS_VENTAS)
        except OSError as error:
            raise ArchivoDatosError(f"No se pudo abrir las ventas: {error}") from error
        return ventas

    def guardar_venta(self, venta: Venta) -> None:
        """Agrega una venta al final del archivo de ventas (modo append).

        Args:
            venta: venta a guardar.

        Raises:
            ArchivoDatosError: si no se puede escribir el archivo.
        """
        if not self._ruta_ventas.exists():
            self._crear_archivo(self._ruta_ventas, self.ENCABEZADOS_VENTAS)
        try:
            with open(self._ruta_ventas, "a", newline="", encoding="utf-8") as archivo:
                csv.writer(archivo).writerow(venta.a_fila_csv())
        except OSError as error:
            raise ArchivoDatosError(f"No se pudo guardar la venta: {error}") from error
