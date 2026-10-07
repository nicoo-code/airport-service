from abc import ABC, abstractmethod

from src.domain.models.airport import Airport


class ExternalAirportPort(ABC):
    """Puerto primario/secundario para la obtención remota de aeropuertos desde proveedores externos."""

    @abstractmethod
    async def get_all_airports(self) -> list[Airport]:
        """Obtiene la lista completa de aeropuertos adaptados al modelo del dominio."""

    @abstractmethod
    async def get_airport_by_id(self, airport_id: int) -> Airport | None:
        """Obtiene un aeropuerto específico por su identificador único."""
