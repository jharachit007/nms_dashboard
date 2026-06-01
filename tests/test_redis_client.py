from app.core.config import Settings
from app.services.redis_client import RedisClient


def test_redis_client_falls_back_when_disabled() -> None:
    client = RedisClient(Settings(redis_enabled=False))

    assert client.get_json("alert:1") is None
    assert client.set_json("alert:1", {"value": "10.20.30.40"}, ttl_seconds=30) is False
    assert client.lpush_json("embedding_queue", {"alert_id": 1}) is False
    assert client.rpop_json("embedding_queue") is None
