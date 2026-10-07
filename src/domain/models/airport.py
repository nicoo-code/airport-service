from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class Airport:
    """Entidad pura del dominio para representar un aeropuerto en el catálogo canónico."""

    id: int
    name: str
    iata_code: str
    city: str
    department: str
    latitude: float
    longitude: float
    type: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
