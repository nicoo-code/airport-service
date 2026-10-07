import asyncio
import time

import pytest
from src.infrastructure.adapters.circuit_breaker import (
    CircuitBreaker,
    CircuitBreakerOpenException,
    CircuitState,
)


@pytest.mark.asyncio
async def test_circuit_breaker_starts_closed():
    cb = CircuitBreaker(failure_threshold=3, recovery_timeout=1.0)
    assert cb.state == CircuitState.CLOSED
    assert cb.failure_count == 0

    async def successful_call():
        return "success"

    res = await cb.call(successful_call)
    assert res == "success"
    assert cb.state == CircuitState.CLOSED


@pytest.mark.asyncio
async def test_circuit_breaker_trips_to_open_after_threshold_failures():
    cb = CircuitBreaker(failure_threshold=3, recovery_timeout=1.0)

    async def failing_call():
        raise ValueError("Simulated network timeout")

    # Intentos 1 y 2
    for _ in range(2):
        with pytest.raises(ValueError):
            await cb.call(failing_call)
        assert cb.state == CircuitState.CLOSED

    # Intento 3: alcanza el umbral y abre el circuito
    with pytest.raises(ValueError):
        await cb.call(failing_call)

    assert cb.state == CircuitState.OPEN
    assert cb.failure_count == 3

    # Inmediatamente después debe fallar rápido lanzando CircuitBreakerOpenException
    with pytest.raises(CircuitBreakerOpenException):
        await cb.call(failing_call)


@pytest.mark.asyncio
async def test_circuit_breaker_uses_fallback_when_open():
    cb = CircuitBreaker(failure_threshold=2, recovery_timeout=1.0)

    async def failing_call():
        raise ConnectionError("External API down")

    def fallback_call():
        return "cached_fallback_data"

    # Fallar 2 veces para abrir
    for _ in range(2):
        res = await cb.call(failing_call, fallback=fallback_call)
        assert res == "cached_fallback_data"

    assert cb.state == CircuitState.OPEN

    # Llamada en estado OPEN usa fallback de inmediato
    start_time = time.time()
    res = await cb.call(failing_call, fallback=fallback_call)
    duration = time.time() - start_time

    assert res == "cached_fallback_data"
    assert duration < 0.05  # Fail-fast en menos de 50ms


@pytest.mark.asyncio
async def test_circuit_breaker_transitions_to_half_open_and_resets():
    cb = CircuitBreaker(failure_threshold=1, recovery_timeout=0.2)

    async def failing_call():
        raise RuntimeError("Fail once")

    async def ok_call():
        return "recovered"

    # Forzar apertura
    with pytest.raises(RuntimeError):
        await cb.call(failing_call)
    assert cb.state == CircuitState.OPEN

    # Esperar ventana de recuperación
    await asyncio.sleep(0.25)

    # La siguiente llamada debe ser prueba en HALF-OPEN y restablecer a CLOSED si tiene éxito
    res = await cb.call(ok_call)
    assert res == "recovered"
    assert cb.state == CircuitState.CLOSED
    assert cb.failure_count == 0
