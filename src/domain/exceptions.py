"""
Excepciones del Dominio para Airport Service.
Encapsulan los errores de negocio desacoplados de cualquier tecnología de infraestructura o framework.
"""


class AirportDomainException(Exception):
    """Excepción base para todos los errores de dominio de aeropuertos."""

    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


class AirportNotFoundException(AirportDomainException):
    """Lanzada cuando un aeropuerto solicitado no existe en el catálogo canónico."""

    def __init__(self, airport_id: int):
        super().__init__(f"El aeropuerto con ID {airport_id} no fue encontrado en el catálogo.")
        self.airport_id = airport_id


class ExternalApiException(AirportDomainException):
    """Lanzada cuando la API externa no está disponible o falla persistentemente."""

    def __init__(self, detail: str):
        super().__init__(f"Fallo en la comunicación con la API externa de aeropuertos: {detail}")
        self.detail = detail


class CircuitBreakerOpenException(AirportDomainException):
    """Lanzada cuando el circuito de resiliencia se encuentra en estado ABIERTO (Fail-fast)."""

    def __init__(self, circuit_name: str = "AirportCircuitBreaker"):
        super().__init__(f"El Circuit Breaker '{circuit_name}' está ABIERTO. Petición rechazada rápidamente.")
        self.circuit_name = circuit_name
