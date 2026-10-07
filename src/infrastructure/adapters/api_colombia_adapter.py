import asyncio
import logging
import random
from typing import Any

import httpx
from src.domain.models.airport import Airport
from src.domain.ports.external_airport_port import ExternalAirportPort
from src.infrastructure.adapters.circuit_breaker import (
    CircuitBreaker,
    CircuitBreakerOpenException,
)

logger = logging.getLogger(__name__)

# Semilla canónica de fallback en caso de desconexión extrema o circuito abierto
FALLBACK_AIRPORTS_DATA = [
    {
        "id": 1,
        "name": "Aeropuerto Internacional El Dorado",
        "iataCode": "BOG",
        "city": {"name": "Bogotá"},
        "department": {"name": "Cundinamarca"},
        "latitude": 4.7016,
        "longitude": -74.1469,
        "type": "Internacional",
    },
    {
        "id": 5,
        "name": "Aeropuerto Internacional José María Córdova",
        "iataCode": "MDE",
        "city": {"name": "Medellín"},
        "department": {"name": "Antioquia"},
        "latitude": 6.1645,
        "longitude": -75.4231,
        "type": "Internacional",
    },
    {
        "id": 9,
        "name": "Aeropuerto Internacional Alfonso Bonilla Aragón",
        "iataCode": "CLO",
        "city": {"name": "Cali"},
        "department": {"name": "Valle del Cauca"},
        "latitude": 3.5432,
        "longitude": -76.3816,
        "type": "Internacional",
    },
    {
        "id": 12,
        "name": "Aeropuerto Internacional Rafael Núñez",
        "iataCode": "CTG",
        "city": {"name": "Cartagena"},
        "department": {"name": "Bolívar"},
        "latitude": 10.4424,
        "longitude": -75.5129,
        "type": "Internacional",
    },
    {
        "id": 15,
        "name": "Aeropuerto Internacional Ernesto Cortissoz",
        "iataCode": "BAQ",
        "city": {"name": "Barranquilla"},
        "department": {"name": "Atlántico"},
        "latitude": 10.8896,
        "longitude": -74.7808,
        "type": "Internacional",
    },
    {
        "id": 18,
        "name": "Aeropuerto Internacional Palonegro",
        "iataCode": "BGA",
        "city": {"name": "Bucaramanga"},
        "department": {"name": "Santander"},
        "latitude": 7.1265,
        "longitude": -73.1848,
        "type": "Nacional",
    },
    {
        "id": 22,
        "name": "Aeropuerto Internacional Matecaña",
        "iataCode": "PEI",
        "city": {"name": "Pereira"},
        "department": {"name": "Risaralda"},
        "latitude": 4.8125,
        "longitude": -75.7397,
        "type": "Internacional",
    },
    {
        "id": 25,
        "name": "Aeropuerto Internacional Gustavo Rojas Pinilla",
        "iataCode": "ADZ",
        "city": {"name": "San Andrés"},
        "department": {"name": "San Andrés y Providencia"},
        "latitude": 12.5833,
        "longitude": -81.7119,
        "type": "Internacional",
    },
]


class ApiColombiaAdapter(ExternalAirportPort):
    """
    Adaptador formal para la API pública de Colombia.
    Implementa el patrón Adapter traduciendo contratos externos a entidades de dominio internas.
    Protegido con Circuit Breaker y Reintentos con Exponential Backoff y Jitter.
    """

    def __init__(
        self,
        base_url: str = "https://api-colombia.com/api/v1/Airport",
        circuit_breaker: CircuitBreaker | None = None,
        timeout: float = 4.0,
        max_retries: int = 3,
    ):
        self.base_url = base_url
        self.timeout = timeout
        self.max_retries = max_retries
        self.circuit_breaker = circuit_breaker or CircuitBreaker(
            failure_threshold=3, recovery_timeout=30.0, name="ApiColombiaCircuitBreaker"
        )

    def _map_to_domain(self, raw: dict[str, Any]) -> Airport:
        """Traduce la representación JSON externa al modelo inmutable Airport del dominio."""
        # Extraer ciudad de estructura anidada o string
        city_raw = raw.get("city")
        city_name = (
            city_raw.get("name")
            if isinstance(city_raw, dict)
            else (str(city_raw) if city_raw else "Desconocida")
        )

        # Extraer departamento de estructura anidada o string
        dept_raw = raw.get("department")
        dept_name = (
            dept_raw.get("name")
            if isinstance(dept_raw, dict)
            else (str(dept_raw) if dept_raw else "Desconocido")
        )

        return Airport(
            id=int(raw.get("id", 0)),
            name=str(raw.get("name", "Aeropuerto Sin Nombre")),
            iata_code=str(raw.get("iataCode") or raw.get("iata_code") or "N/A"),
            city=city_name,
            department=dept_name,
            latitude=float(raw.get("latitude", 0.0) or 0.0),
            longitude=float(raw.get("longitude", 0.0) or 0.0),
            type=str(raw.get("type", "Nacional")),
        )

    async def _execute_http_with_retry(self, url: str) -> httpx.Response:
        """Ejecuta petición HTTP con reintentos exponenciales y jitter."""
        last_exception = None
        for attempt in range(1, self.max_retries + 1):
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.get(url)
                    response.raise_for_status()
                    return response
            except (httpx.RequestError, httpx.HTTPStatusError) as exc:
                last_exception = exc
                if attempt < self.max_retries:
                    # Exponential backoff base 0.5s con jitter
                    backoff = (0.5 * (2 ** (attempt - 1))) + random.uniform(0.0, 0.1)
                    logger.warning(
                        f"Attempt {attempt} failed calling '{url}': {exc}. Retrying in {backoff:.2f}s..."
                    )
                    await asyncio.sleep(backoff)
                else:
                    logger.error(
                        f"All {self.max_retries} attempts failed calling '{url}': {exc}"
                    )
        raise last_exception

    async def get_all_airports(self) -> list[Airport]:
        """Obtiene la lista de aeropuertos a través del Circuit Breaker con fallback seguro."""

        async def _fetch():
            response = await self._execute_http_with_retry(self.base_url)
            data = response.json()
            if not isinstance(data, list):
                data = [data]
            return [self._map_to_domain(item) for item in data if item.get("id")]

        def _fallback():
            logger.info(
                "Executing fallback: Serving canonical default airports catalog"
            )
            return [self._map_to_domain(item) for item in FALLBACK_AIRPORTS_DATA]

        try:
            return await self.circuit_breaker.call(_fetch, fallback=_fallback)
        except CircuitBreakerOpenException:
            logger.warning("Circuit breaker is open, executing direct fallback")
            return _fallback()
        except (
            httpx.HTTPError,
            TimeoutError,
            ValueError,
            KeyError,
            OSError,
            RuntimeError,
        ) as e:
            logger.error(
                f"Error fetching airports from external API: {e}. Using fallback."
            )
            return _fallback()

    async def get_airport_by_id(self, airport_id: int) -> Airport | None:
        """Obtiene un aeropuerto por su ID."""
        url = f"{self.base_url}/{airport_id}"

        async def _fetch_one():
            response = await self._execute_http_with_retry(url)
            data = response.json()
            if data and isinstance(data, dict):
                return self._map_to_domain(data)
            return None

        def _fallback_one():
            for item in FALLBACK_AIRPORTS_DATA:
                if item["id"] == airport_id:
                    return self._map_to_domain(item)
            return None

        try:
            return await self.circuit_breaker.call(_fetch_one, fallback=_fallback_one)
        except (
            httpx.HTTPError,
            CircuitBreakerOpenException,
            TimeoutError,
            ValueError,
            KeyError,
            OSError,
            RuntimeError,
        ) as e:
            logger.error(
                f"Error fetching airport {airport_id}: {e}. Checking fallback."
            )
            return _fallback_one()
