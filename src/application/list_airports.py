import json
import logging

from src.domain.models.airport import Airport
from src.domain.ports.cache_port import CachePort
from src.domain.ports.external_airport_port import ExternalAirportPort

logger = logging.getLogger(__name__)

CACHE_KEY_AIRPORTS = "airports:all:catalog"


class ListAirportsUseCase:
    """Caso de uso para listar todos los aeropuertos integrando caché en memoria y resiliencia."""

    def __init__(self, external_port: ExternalAirportPort, cache_port: CachePort):
        self._external_port = external_port
        self._cache_port = cache_port

    async def execute(self) -> list[Airport]:
        # 1. Intentar recuperar desde la caché
        try:
            cached_data = await self._cache_port.get(CACHE_KEY_AIRPORTS)
            if cached_data:
                logger.info("Retrieved airports catalog from cache hit")
                raw_list = json.loads(cached_data)
                return [Airport(**item) for item in raw_list]
        except (RuntimeError, ValueError, KeyError, OSError) as e:
            logger.warning(f"Failed to read from cache port: {e}")

        # 2. Si no hay cache hit, consultar puerto externo
        airports = await self._external_port.get_all_airports()

        # 3. Guardar en caché asíncronamente
        if airports:
            try:
                serialized = json.dumps([a.to_dict() for a in airports])
                await self._cache_port.set(
                    CACHE_KEY_AIRPORTS, serialized, ttl_seconds=3600
                )
                logger.info(f"Stored {len(airports)} airports in cache for 1 hour")
            except (RuntimeError, ValueError, TypeError, OSError) as e:
                logger.warning(f"Failed to persist airports to cache: {e}")

        return airports
