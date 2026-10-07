import pytest

from src.domain.models.airport import Airport
from src.infrastructure.adapters.api_colombia_adapter import ApiColombiaAdapter


def test_map_raw_json_to_domain():
    adapter = ApiColombiaAdapter()
    raw_external = {
        "id": 101,
        "name": "Aeropuerto Benito Salas",
        "iataCode": "NVA",
        "city": {"name": "Neiva"},
        "department": {"name": "Huila"},
        "latitude": 2.9501,
        "longitude": -75.2941,
        "type": "Nacional",
    }

    airport = adapter._map_to_domain(raw_external)
    assert isinstance(airport, Airport)
    assert airport.id == 101
    assert airport.name == "Aeropuerto Benito Salas"
    assert airport.iata_code == "NVA"
    assert airport.city == "Neiva"
    assert airport.department == "Huila"
    assert airport.latitude == 2.9501
    assert airport.longitude == -75.2941
    assert airport.type == "Nacional"


def test_map_raw_json_with_flat_strings():
    adapter = ApiColombiaAdapter()
    raw_flat = {
        "id": 202,
        "name": "Aeropuerto La Nubia",
        "iata_code": "MZL",
        "city": "Manizales",
        "department": "Caldas",
        "latitude": 5.0297,
        "longitude": -75.4655,
        "type": "Nacional",
    }

    airport = adapter._map_to_domain(raw_flat)
    assert airport.id == 202
    assert airport.city == "Manizales"
    assert airport.department == "Caldas"
    assert airport.iata_code == "MZL"


@pytest.mark.asyncio
async def test_get_all_airports_returns_fallback_on_network_error():
    adapter = ApiColombiaAdapter(
        base_url="http://invalid-host-unreachable:9999", max_retries=1, timeout=0.1
    )

    airports = await adapter.get_all_airports()
    assert len(airports) >= 5
    assert any(a.iata_code == "BOG" for a in airports)
    assert any(a.iata_code == "MDE" for a in airports)


@pytest.mark.asyncio
async def test_get_airport_by_id_returns_fallback():
    adapter = ApiColombiaAdapter(
        base_url="http://invalid-host-unreachable:9999", max_retries=1, timeout=0.1
    )
    airport = await adapter.get_airport_by_id(1)
    assert airport is not None
    assert airport.id == 1
    assert airport.iata_code == "BOG"
