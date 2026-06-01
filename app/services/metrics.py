import time
from collections import defaultdict, deque
from threading import RLock


class MetricsRegistry:
    def __init__(self) -> None:
        self._counters: dict[str, float] = defaultdict(float)
        self._timings: dict[str, deque[float]] = defaultdict(lambda: deque(maxlen=200))
        self._gauges: dict[str, float] = {}
        self._lock = RLock()

    def increment(self, name: str, value: float = 1.0) -> None:
        with self._lock:
            self._counters[name] += value

    def observe_latency(self, name: str, seconds: float) -> None:
        with self._lock:
            self._timings[name].append(seconds)

    def set_gauge(self, name: str, value: float) -> None:
        with self._lock:
            self._gauges[name] = value

    def snapshot(self) -> dict:
        with self._lock:
            timings = {}
            for name, values in self._timings.items():
                sample = list(values)
                timings[name] = {
                    "count": len(sample),
                    "avg_ms": round((sum(sample) / len(sample)) * 1000, 2) if sample else 0,
                    "max_ms": round(max(sample) * 1000, 2) if sample else 0,
                }
            return {
                "timestamp": int(time.time()),
                "counters": dict(self._counters),
                "gauges": dict(self._gauges),
                "timings": timings,
            }

    def reset(self) -> None:
        with self._lock:
            self._counters.clear()
            self._timings.clear()
            self._gauges.clear()


metrics_registry = MetricsRegistry()
