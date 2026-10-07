from src.domain.models.airport import Airport
from src.infrastructure.adapters.plotly_adapter import PlotlyAdapter


def test_plotly_adapter_formatting():
    adapter = PlotlyAdapter()
    airports = [
        Airport(
            id=1,
            name="El Dorado",
            iata_code="BOG",
            city="Bogotá",
            department="Cundinamarca",
            latitude=4.7016,
            longitude=-74.1469,
            type="Internacional",
        ),
        Airport(
            id=5,
            name="José María Córdova",
            iata_code="MDE",
            city="Medellín",
            department="Antioquia",
            latitude=6.1645,
            longitude=-75.4231,
            type="Internacional",
        ),
        Airport(
            id=99,
            name="Sin Coordenadas",
            iata_code="XXX",
            city="Ciudad",
            department="Depto",
            latitude=0.0,
            longitude=0.0,
            type="Nacional",
        ),
    ]

    result = adapter.format_for_scattergeo(airports)
    assert "data" in result
    assert "layout" in result
    assert len(result["data"]) == 1

    trace = result["data"][0]
    assert trace["type"] == "scattergeo"
    assert trace["lat"] == [4.7016, 6.1645]  # El aeropuerto con 0.0 debe ser filtrado
    assert trace["lon"] == [-74.1469, -75.4231]
    assert trace["text"] == ["BOG", "MDE"]
    assert trace["ids"] == [1, 5]
    assert result["count"] == 2
