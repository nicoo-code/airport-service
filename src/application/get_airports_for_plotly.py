from typing import Any

from src.application.list_airports import ListAirportsUseCase


class GetAirportsForPlotlyUseCase:
    """Caso de uso para transformar la lista de aeropuertos de dominio al formato específico de Plotly JS."""

    def __init__(self, list_use_case: ListAirportsUseCase, plotly_adapter):
        self._list_use_case = list_use_case
        self._plotly_adapter = plotly_adapter

    async def execute(self) -> dict[str, Any]:
        airports = await self._list_use_case.execute()
        return self._plotly_adapter.format_for_scattergeo(airports)
