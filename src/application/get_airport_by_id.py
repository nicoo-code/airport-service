import logging

from src.application.list_airports import ListAirportsUseCase
from src.domain.models.airport import Airport
from src.domain.ports.external_airport_port import ExternalAirportPort

logger = logging.getLogger(__name__)


class GetAirportByIdUseCase:
    """Caso de uso para buscar y validar un aeropuerto específico por su ID."""

    def __init__(
        self,
        external_port: ExternalAirportPort,
        list_use_case: ListAirportsUseCase | None = None,
    ):
        self._external_port = external_port
        self._list_use_case = list_use_case

    async def execute(self, airport_id: int) -> Airport | None:
        # Primero intentar por ID directo
        airport = await self._external_port.get_airport_by_id(airport_id)
        if airport:
            return airport

        # Si el endpoint individual no lo devuelve directamente, buscar en la lista completa (cache o catálogo)
        if self._list_use_case:
            all_airports = await self._list_use_case.execute()
            for a in all_airports:
                if a.id == airport_id:
                    return a

        logger.info(f"Airport with ID {airport_id} not found in catalog")
        return None
