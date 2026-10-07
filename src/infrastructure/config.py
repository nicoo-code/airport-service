import os

from pydantic import BaseModel


class Settings(BaseModel):
    service_name: str = "airport-service"
    service_port: int = int(os.getenv("PORT", "8001"))
    api_colombia_url: str = os.getenv(
        "API_COLOMBIA_URL", "https://api-colombia.com/api/v1/Airport"
    )
    redis_url: str = os.getenv("REDIS_URL", "redis://redis:6379/0")
    otlp_endpoint: str = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://jaeger:4317")
    log_level: str = os.getenv("LOG_LEVEL", "INFO")


settings = Settings()
