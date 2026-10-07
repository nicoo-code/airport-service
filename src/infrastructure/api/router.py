from fastapi import APIRouter, HTTPException, status
from src.application.get_airport_by_id import GetAirportByIdUseCase
from src.application.get_airports_for_plotly import GetAirportsForPlotlyUseCase
from src.application.list_airports import ListAirportsUseCase
from src.infrastructure.api.schemas import AirportResponse, HealthCheckResponse


def create_airport_router(
    list_airports_use_case: ListAirportsUseCase,
    get_airport_by_id_use_case: GetAirportByIdUseCase,
    get_plotly_use_case: GetAirportsForPlotlyUseCase,
    redis_adapter,
    circuit_breaker,
) -> APIRouter:
    router = APIRouter(prefix="", tags=["Airports"])

    @router.get(
        "/api/v1/airports",
        response_model=list[AirportResponse],
        summary="Listar todos los aeropuertos",
        description="Retorna el catálogo canónico completo de aeropuertos colombianos adaptado al dominio.",
    )
    async def get_airports():
        airports = await list_airports_use_case.execute()
        return [AirportResponse.model_validate(a.to_dict()) for a in airports]

    @router.get(
        "/api/v1/airports/map/plotly",
        summary="Obtener estructura Scattergeo de Plotly JS",
        description="Retorna las coordenadas, marcas y metadatos formateados específicamente para Plotly.newPlot().",
    )
    async def get_plotly_map():
        return await get_plotly_use_case.execute()

    @router.get(
        "/api/v1/airports/{airport_id}",
        response_model=AirportResponse,
        summary="Buscar aeropuerto por ID",
        description="Retorna los datos de un aeropuerto específico. Utilizado por Itinerary Service para validación síncrona.",
    )
    async def get_airport(airport_id: int):
        airport = await get_airport_by_id_use_case.execute(airport_id)
        if not airport:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Aeropuerto con ID {airport_id} no encontrado en el catálogo.",
            )
        return AirportResponse.model_validate(airport.to_dict())

    @router.get(
        "/health",
        response_model=HealthCheckResponse,
        tags=["Health"],
        summary="Healthcheck y estado de dependencias",
    )
    async def healthcheck():
        redis_ok = await redis_adapter.ping()
        cb_status = circuit_breaker.get_status()
        return HealthCheckResponse(
            status="UP",
            service="airport-service",
            redis_connected=redis_ok,
            circuit_breaker=cb_status,
        )

    return router
