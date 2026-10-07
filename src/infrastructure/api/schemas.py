from pydantic import BaseModel, ConfigDict, Field


class AirportResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int = Field(..., description="ID único del aeropuerto")
    name: str = Field(..., description="Nombre oficial del aeropuerto")
    iata_code: str = Field(..., description="Código IATA de 3 letras")
    city: str = Field(..., description="Ciudad en la que opera")
    department: str = Field(..., description="Departamento de Colombia")
    latitude: float = Field(..., description="Coordenada de latitud")
    longitude: float = Field(..., description="Coordenada de longitud")
    type: str = Field(
        ..., description="Tipo de terminal (Internacional, Nacional, etc.)"
    )


class CircuitBreakerStatusResponse(BaseModel):
    name: str
    state: str
    failure_count: int
    failure_threshold: int
    recovery_timeout: float
    last_failure_time: float


class HealthCheckResponse(BaseModel):
    status: str
    service: str
    redis_connected: bool
    circuit_breaker: CircuitBreakerStatusResponse
