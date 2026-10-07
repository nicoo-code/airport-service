from abc import ABC, abstractmethod


class CachePort(ABC):
    """Puerto abstracto para el mecanismo de almacenamiento en caché de alto rendimiento."""

    @abstractmethod
    async def get(self, key: str) -> str | None:
        """Recupera un valor de la memoria caché por su clave."""

    @abstractmethod
    async def set(self, key: str, value: str, ttl_seconds: int = 3600) -> None:
        """Almacena un valor serializado en caché con un tiempo de vida (TTL) determinado."""
