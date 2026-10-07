# Airport Service - Microservicio de Aeropuertos Colombianos

[![CI Pipeline](https://github.com/nicoo-code/airport-service/actions/workflows/ci.yml/badge.svg)](https://github.com/nicoo-code/airport-service/actions)
[![Python Version](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110%2B-009688.svg)](https://fastapi.tiangolo.com/)
[![Architecture](https://img.shields.io/badge/Architecture-Hexagonal%20(Ports%20%26%20Adapters)-orange.svg)]()

Microservicio autónomo responsable de consultar, adaptar y enriquecer información de aeropuertos colombianos consumiendo la API pública externa API Colombia, bajo **Arquitectura Hexagonal (Puertos y Adaptadores)**, garantizando alta disponibilidad y resiliencia.

---

## 1. Arquitectura Hexagonal

El servicio desacopla completamente el núcleo de negocio de cualquier detalle tecnológico o proveedor externo:

```
src/
├── domain/                    # Capa de Dominio (Pura, sin dependencias externas)
│   ├── models/                # Entidades inmutables (Airport)
│   ├── ports/                 # Interfaces abstractas (ExternalAirportPort, CachePort)
│   └── exceptions.py          # Excepciones de negocio (AirportNotFoundException, etc.)
├── application/               # Capa de Aplicación (Casos de uso orquestadores)
│   ├── list_airports.py       # ListAirportsUseCase (con cache-aside)
│   ├── get_airport_by_id.py   # GetAirportByIdUseCase
│   └── get_airports_for_plotly.py # Formateo geoespacial para frontend
└── infrastructure/            # Capa de Infraestructura (Adaptadores y Frameworks)
    ├── adapters/
    │   ├── api_colombia_adapter.py # Adapter formal para API Colombia
    │   ├── circuit_breaker.py      # Máquina de estados Circuit Breaker
    │   ├── plotly_adapter.py       # Adapter de ScatterGeo para Plotly JS
    │   └── redis_cache_adapter.py  # Cache con Redis y fallback en memoria
    ├── api/                   # Controladores FastAPI y Esquemas Pydantic v2
    │   ├── router.py
    │   └── schemas.py
    ├── config.py              # Configuración y variables de entorno
    └── main.py                # Inicialización de la aplicación FastAPI y middlewares
```

---

## 2. Patrones Arquitectónicos y Resiliencia

1. **Patrón Adapter Formal:**
   - La API pública (`https://api-colombia.com/api/v1/Airport`) posee un esquema heterogéneo (objetos anidados en ciudad/departamento, nombres de campos cambiantes).
   - `ApiColombiaAdapter` implementa `ExternalAirportPort` y traduce la respuesta externa al modelo canónico inmutable `Airport`.
   - Si la API externa cambia, únicamente se actualiza el adaptador; la aplicación y el dominio permanecen intactos.

2. **Circuit Breaker (Tolerancia a Fallos):**
   - Implementa una máquina de estados formal: `CLOSED`, `OPEN`, `HALF_OPEN`.
   - Umbral de 3 fallos consecutivos abre el circuito.
   - En estado `OPEN`, opera en modo **Fail-Fast** (< 5ms) retornando un catálogo canónico de fallback seguro.
   - Ventana de recuperación de 30s para probar restablecimiento.

3. **Reintentos con Exponential Backoff y Jitter:**
   - 3 reintentos con factor base de 0.5s exponencial y jitter aleatorio (0-100ms) para evitar problemas de rebaño (Thundering Herd).

4. **Capa de Caché con Redis:**
   - Estrategia Cache-Aside con TTL de 3600s para reducir drásticamente el consumo de peticiones hacia la API externa.
   - Fallback transparente en memoria si Redis no está disponible.

5. **Observabilidad y Tracing:**
   - Logs estructurados en formato JSON (`timestamp`, `level`, `service`, `trace_id`, `span_id`).
   - Soporte para W3C Trace Context (`traceparent`).

---

## 3. Endpoints REST (OpenAPI / Swagger)

La documentación interactiva Swagger está disponible en `/docs` y ReDoc en `/redoc`.

| Método | Endpoint | Descripción |
| :--- | :--- | :--- |
| `GET` | `/api/v1/airports` | Retorna el catálogo canónico completo de aeropuertos colombianos. |
| `GET` | `/api/v1/airports/{airport_id}` | Retorna el detalle de un aeropuerto específico (usado para validación). |
| `GET` | `/api/v1/airports/map/plotly` | Retorna coordenadas y marcas optimizadas para `Plotly.newPlot()`. |
| `GET` | `/health` | Healthcheck y estado de dependencias (Redis y Circuit Breaker). |

---

## 4. Ejecución Local y Docker

### Ejecución con Python local:
```bash
# Crear entorno virtual e instalar dependencias
python -m venv venv
source venv/bin/activate  # En Windows: .\venv\Scripts\activate
pip install -r requirements.txt

# Ejecutar el servicio
uvicorn src.main:app --host 0.0.0.0 --port 8001 --reload
```

### Ejecución independiente con Docker Compose:
```bash
docker compose up --build
```

---

## 5. Pruebas Automatizadas

```bash
# Ejecutar suite de pruebas unitarias e integración con cobertura
pytest tests/ -v --cov=src --cov-report=term --cov-report=xml:coverage.xml
```

---

## 6. Variables de Entorno

| Variable | Valor por Defecto | Descripción |
| :--- | :--- | :--- |
| `PORT` | `8001` | Puerto HTTP del servicio |
| `API_COLOMBIA_URL` | `https://api-colombia.com/api/v1/Airport` | URL de la API externa |
| `REDIS_URL` | `redis://redis:6379/0` | Cadena de conexión a Redis |
| `LOG_LEVEL` | `INFO` | Nivel de logging estructurado |
