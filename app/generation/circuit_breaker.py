from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field
from enum import Enum


class CircuitState(Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


@dataclass
class CircuitBreakerConfig:
    failure_threshold: int = 5
    success_threshold: int = 2
    timeout_seconds: float = 30.0
    half_open_max_calls: int = 3


@dataclass
class CircuitBreaker:
    name: str
    config: CircuitBreakerConfig = field(default_factory=CircuitBreakerConfig)
    _state: CircuitState = field(default=CircuitState.CLOSED, init=False)
    _failure_count: int = field(default=0, init=False)
    _success_count: int = field(default=0, init=False)
    _last_failure_time: float | None = field(default=None, init=False)
    _half_open_calls: int = field(default=0, init=False)
    _lock: threading.Lock = field(default_factory=threading.Lock, init=False)

    @property
    def state(self) -> CircuitState:
        with self._lock:
            if self._state == CircuitState.OPEN and self._should_attempt_reset():
                self._state = CircuitState.HALF_OPEN
                self._half_open_calls = 0
            return self._state

    @property
    def is_available(self) -> bool:
        return self.state != CircuitState.OPEN

    def _should_attempt_reset(self) -> bool:
        if self._last_failure_time is None:
            return True
        return (time.time() - self._last_failure_time) >= self.config.timeout_seconds

    def record_success(self) -> None:
        with self._lock:
            self._failure_count = 0
            self._last_failure_time = None
            self._success_count += 1
            self._last_success_time = time.time()
            if self._state == CircuitState.HALF_OPEN:
                if self._success_count >= self.config.success_threshold:
                    self._state = CircuitState.CLOSED
                    self._success_count = 0
            elif self._state == CircuitState.CLOSED:
                self._success_count = 0

    def record_failure(self) -> None:
        with self._lock:
            self._failure_count += 1
            self._success_count = 0
            self._last_failure_time = time.time()
            if self._state == CircuitState.HALF_OPEN:
                self._state = CircuitState.OPEN
            elif self._failure_count >= self.config.failure_threshold:
                self._state = CircuitState.OPEN

    def record_half_open_call(self) -> bool:
        with self._lock:
            if self._state != CircuitState.HALF_OPEN:
                return False
            if self._half_open_calls >= self.config.half_open_max_calls:
                return False
            self._half_open_calls += 1
            return True

    def get_state(self) -> dict:
        with self._lock:
            return {
                "name": self.name,
                "state": self._state.value,
                "failure_count": self._failure_count,
                "success_count": self._success_count,
                "last_failure_time": self._last_failure_time,
                "timeout_seconds": self.config.timeout_seconds,
            }

    def reset(self) -> None:
        with self._lock:
            self._state = CircuitState.CLOSED
            self._failure_count = 0
            self._success_count = 0
            self._half_open_calls = 0
            self._last_failure_time = None


_CIRCUIT_BREAKERS: dict[str, CircuitBreaker] = {}
_BREAKER_LOCK = threading.Lock()


def get_circuit_breaker(name: str, config: CircuitBreakerConfig | None = None) -> CircuitBreaker:
    with _BREAKER_LOCK:
        if name not in _CIRCUIT_BREAKERS:
            _CIRCUIT_BREAKERS[name] = CircuitBreaker(name, config or CircuitBreakerConfig())
        return _CIRCUIT_BREAKERS[name]
