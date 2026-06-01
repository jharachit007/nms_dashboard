from app.services.cache import TTLCache
from app.services.metrics import MetricsRegistry


def test_ttl_cache_get_set_and_prefix_invalidation() -> None:
    cache = TTLCache()
    cache.set("alerts:critical", [{"id": 1}], ttl_seconds=60)
    cache.set("recommendation:1", {"id": 2}, ttl_seconds=60)

    assert cache.get("alerts:critical") == [{"id": 1}]
    assert cache.invalidate_prefix("alerts:") == 1
    assert cache.get("alerts:critical") is None
    assert cache.get("recommendation:1") == {"id": 2}


def test_metrics_registry_tracks_counters_gauges_and_latency() -> None:
    metrics = MetricsRegistry()
    metrics.increment("alerts_ingested_count", 3)
    metrics.set_gauge("active_alert_count", 2)
    metrics.observe_latency("api_request_latency", 0.25)

    snapshot = metrics.snapshot()

    assert snapshot["counters"]["alerts_ingested_count"] == 3
    assert snapshot["gauges"]["active_alert_count"] == 2
    assert snapshot["timings"]["api_request_latency"]["count"] == 1
