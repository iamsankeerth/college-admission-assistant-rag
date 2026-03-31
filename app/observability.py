from __future__ import annotations

import logging
import time
from functools import wraps
from typing import Any, Callable

from app.config import settings

logger = logging.getLogger("app.observability")


class MetricsCollector:
    def __init__(self) -> None:
        self._counters: dict[str, float] = {}
        self._histograms: dict[str, list[float]] = {}
        self._gauges: dict[str, float] = {}

    def increment(self, name: str, value: float = 1.0, labels: dict[str, str] | None = None) -> None:
        key = self._make_key(name, labels)
        self._counters[key] = self._counters.get(key, 0) + value

    def record(self, name: str, value: float, labels: dict[str, str] | None = None) -> None:
        key = self._make_key(name, labels)
        if key not in self._histograms:
            self._histograms[key] = []
        self._histograms[key].append(value)

    def gauge(self, name: str, value: float, labels: dict[str, str] | None = None) -> None:
        key = self._make_key(name, labels)
        self._gauges[key] = value

    def _make_key(self, name: str, labels: dict[str, str] | None) -> str:
        if not labels:
            return name
        label_str = ",".join(f"{k}={v}" for k, v in sorted(labels.items()))
        return f"{name}{{{label_str}}}"

    def get_all(self) -> dict[str, Any]:
        output: dict[str, Any] = {}
        for key, value in self._counters.items():
            output[f"counter_{key}"] = value
        for key, values in self._histograms.items():
            if values:
                sorted_vals = sorted(values)
                n = len(sorted_vals)
                output[f"histogram_{key}_count"] = n
                output[f"histogram_{key}_sum"] = sum(sorted_vals)
                output[f"histogram_{key}_p50"] = sorted_vals[n // 2]
                output[f"histogram_{key}_p95"] = sorted_vals[int(n * 0.95)] if n > 1 else sorted_vals[0]
                output[f"histogram_{key}_p99"] = sorted_vals[int(n * 0.99)] if n > 1 else sorted_vals[0]
        for key, value in self._gauges.items():
            output[f"gauge_{key}"] = value
        return output

    def reset(self) -> None:
        self._counters.clear()
        self._histograms.clear()
        self._gauges.clear()


_metrics = MetricsCollector()


def get_metrics() -> MetricsCollector:
    return _metrics


class Timer:
    __slots__ = ("_start", "_labels")

    def __init__(self, labels: dict[str, str] | None = None) -> None:
        self._start = time.perf_counter()
        self._labels = labels or {}

    def stop(self, metric_name: str) -> float:
        elapsed = time.perf_counter() - self._start
        if settings.metrics_enabled:
            _metrics.record(metric_name, elapsed * 1000, self._labels)
        return elapsed


def timed(metric_name: str | None = None, labels: dict[str, str] | None = None) -> Callable:
    def decorator(func: Callable) -> Callable:
        name = metric_name or func.__name__

        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            timer = Timer(labels)
            try:
                result = func(*args, **kwargs)
                _metrics.increment(f"{name}.success", labels=labels)
                return result
            except Exception:
                _metrics.increment(f"{name}.error", labels=labels)
                raise
            finally:
                elapsed = timer.stop(name)
                logger.debug(f"{name} took {elapsed*1000:.2f}ms")
        return wrapper
    return decorator


class Span:
    def __init__(self, name: str, labels: dict[str, str] | None = None) -> None:
        self.name = name
        self.labels = labels or {}
        self._start = time.perf_counter()
        self._events: list[dict] = []

    def event(self, name: str, attributes: dict[str, str] | None = None) -> None:
        self._events.append({
            "name": name,
            "timestamp": time.time(),
            "attributes": attributes or {},
        })

    def end(self) -> dict:
        duration_ms = (time.perf_counter() - self._start) * 1000
        return {
            "name": self.name,
            "duration_ms": round(duration_ms, 2),
            "labels": self.labels,
            "events": self._events,
        }


def trace(name: str | None = None, labels: dict[str, str] | None = None) -> Callable:
    def decorator(func: Callable) -> Callable:
        span_name = name or func.__name__

        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            if not settings.tracing_enabled:
                return func(*args, **kwargs)
            span = Span(span_name, labels)
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                span_data = span.end()
                logger.debug(
                    f"span:{span_data['name']} duration_ms={span_data['duration_ms']}"
                )
        return wrapper
    return decorator


def get_tracing_context() -> dict[str, Any]:
    return {}
