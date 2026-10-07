import asyncio
import logging
import time
from collections.abc import Callable
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class CircuitState(str, Enum):
    CLOSED = "CLOSED"
    OPEN = "OPEN"
    HALF_OPEN = "HALF_OPEN"


class CircuitBreakerOpenException(Exception):
    """Excepción lanzada cuando el circuito está abierto y rechaza peticiones fail-fast."""


class CircuitBreaker:
    """Implementación formal de la máquina de estados Circuit Breaker (Closed, Open, Half-Open)."""

    def __init__(
        self,
        failure_threshold: int = 3,
        recovery_timeout: float = 30.0,
        name: str = "CircuitBreaker",
    ):
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.state: CircuitState = CircuitState.CLOSED
        self.failure_count: int = 0
        self.last_failure_time: float = 0.0
        self._lock = asyncio.Lock()

    async def call(
        self, func: Callable, *args, fallback: Callable | None = None, **kwargs
    ) -> Any:
        async with self._lock:
            current_time = time.time()

            # Transición de OPEN a HALF_OPEN trascurrido el tiempo de recuperación
            if self.state == CircuitState.OPEN:
                if current_time - self.last_failure_time >= self.recovery_timeout:
                    logger.info(
                        f"[{self.name}] Transitioning from OPEN to HALF_OPEN (recovery window elapsed)"
                    )
                    self.state = CircuitState.HALF_OPEN
                else:
                    logger.warning(f"[{self.name}] Circuit is OPEN. Fast-failing call.")
                    if fallback:
                        return (
                            await fallback(*args, **kwargs)
                            if asyncio.iscoroutinefunction(fallback)
                            else fallback(*args, **kwargs)
                        )
                    raise CircuitBreakerOpenException(
                        f"Circuit breaker '{self.name}' is OPEN"
                    )

        # Ejecución de la función protegida
        try:
            if asyncio.iscoroutinefunction(func):
                result = await func(*args, **kwargs)
            else:
                result = func(*args, **kwargs)

            # Si tuvo éxito
            await self._on_success()
            return result

        except Exception as exc:
            await self._on_failure(exc)
            if fallback:
                logger.info(f"[{self.name}] Executing fallback due to error: {exc}")
                return (
                    await fallback(*args, **kwargs)
                    if asyncio.iscoroutinefunction(fallback)
                    else fallback(*args, **kwargs)
                )
            raise

    async def _on_success(self):
        async with self._lock:
            if self.state == CircuitState.HALF_OPEN:
                logger.info(
                    f"[{self.name}] Trial call succeeded. Resetting circuit to CLOSED."
                )
            self.state = CircuitState.CLOSED
            self.failure_count = 0

    async def _on_failure(self, exc: Exception):
        async with self._lock:
            self.failure_count += 1
            self.last_failure_time = time.time()
            logger.error(
                f"[{self.name}] Failure #{self.failure_count} recorded. Error: {exc}"
            )

            if (
                self.state in (CircuitState.CLOSED, CircuitState.HALF_OPEN)
                and self.failure_count >= self.failure_threshold
            ):
                self.state = CircuitState.OPEN
                logger.error(
                    f"[{self.name}] Failure threshold {self.failure_threshold} reached. Circuit tripped to OPEN!"
                )

    def get_status(self) -> dict:
        return {
            "name": self.name,
            "state": self.state.value,
            "failure_count": self.failure_count,
            "failure_threshold": self.failure_threshold,
            "recovery_timeout": self.recovery_timeout,
            "last_failure_time": self.last_failure_time,
        }
