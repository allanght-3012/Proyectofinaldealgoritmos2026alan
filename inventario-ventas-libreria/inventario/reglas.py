"""Regla de negocio asignada: descuento por volumen (con herencia y polimorfismo)."""
from __future__ import annotations
from abc import ABC, abstractmethod


class ReglaNegocio(ABC):
    """Clase base abstracta de las reglas de descuento.

    Cada subclase decide qué porcentaje de descuento aplica; el cálculo del
    total es común y lo hace ``aplicar``.
    """

    def __init__(self, nombre: str) -> None:
        """Crea la regla.

        Args:
            nombre: nombre descriptivo de la regla.
        """
        self._nombre: str = nombre

    @property
    def nombre(self) -> str:
        """Nombre descriptivo de la regla."""
        return self._nombre

    @abstractmethod
    def porcentaje_descuento(self, cantidad: int) -> float:
        """Indica el descuento que corresponde a una cantidad.

        Args:
            cantidad: unidades compradas.

        Returns:
            Porcentaje como fracción (0.10 = 10%).
        """

    def aplicar(self, subtotal: float, cantidad: int) -> tuple[float, float]:
        """Aplica la regla a una compra (método polimórfico).

        Args:
            subtotal: precio de la compra sin descuento.
            cantidad: unidades compradas.

        Returns:
            Tupla (porcentaje aplicado, total con descuento redondeado).
        """
        porcentaje = self.porcentaje_descuento(cantidad)
        return porcentaje, round(subtotal * (1 - porcentaje), 2)

    def __str__(self) -> str:
        """Texto legible de la regla."""
        return self._nombre


class SinDescuento(ReglaNegocio):
    """Regla que nunca aplica descuento."""

    def __init__(self) -> None:
        """Crea la regla sin descuento."""
        super().__init__("Sin descuento")

    def porcentaje_descuento(self, cantidad: int) -> float:
        """Devuelve siempre 0.

        Args:
            cantidad: unidades compradas (no influye).

        Returns:
            0.0
        """
        return 0.0


class DescuentoPorVolumen(ReglaNegocio):
    """Descuento que crece con las unidades compradas.

    Por defecto: 5+ unidades 5%, 10+ unidades 10%, 20+ unidades 15%.
    """

    UMBRALES_POR_DEFECTO: tuple = ((20, 0.15), (10, 0.10), (5, 0.05))

    def __init__(self, umbrales: tuple | None = None) -> None:
        """Crea la regla.

        Args:
            umbrales: pares (unidades mínimas, porcentaje). Si es None se
                usan los umbrales por defecto.
        """
        super().__init__("Descuento por volumen")
        self._umbrales: tuple = tuple(
            sorted(umbrales or self.UMBRALES_POR_DEFECTO, reverse=True)
        )

    def porcentaje_descuento(self, cantidad: int) -> float:
        """Busca el mayor umbral que la cantidad alcanza.

        Args:
            cantidad: unidades compradas.

        Returns:
            Porcentaje del umbral alcanzado, o 0.0 si no alcanza ninguno.
        """
        for minimo, porcentaje in self._umbrales:
            if cantidad >= minimo:
                return porcentaje
        return 0.0
