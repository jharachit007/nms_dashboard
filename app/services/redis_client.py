import json
import logging
import time
from functools import lru_cache

from app.core.config import Settings, get_settings
from app.services.sanitization import sanitize_for_llm

logger = logging.getLogger(__name__)


class RedisUnavailable(Exception):
    pass


class RedisClient:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._client = None
        self._disabled_until = 0.0

    @property
    def client(self):
        if not self.settings.redis_enabled:
            raise RedisUnavailable("Redis is disabled")
        if self._disabled_until > time.monotonic():
            raise RedisUnavailable("Redis is temporarily unavailable")
        if self._client is None:
            try:
                import redis

                self._client = redis.Redis.from_url(
                    self.settings.redis_url,
                    socket_timeout=self.settings.redis_socket_timeout_seconds,
                    socket_connect_timeout=self.settings.redis_socket_timeout_seconds,
                    decode_responses=True,
                )
                self._client.ping()
            except Exception as exc:
                self._client = None
                self._disabled_until = time.monotonic() + 30
                raise RedisUnavailable("Redis is unavailable") from exc
        self._disabled_until = 0.0
        return self._client

    def get_json(self, key: str):
        try:
            raw = self.client.get(key)
        except RedisUnavailable:
            return None
        except Exception:
            logger.exception("redis_get_failed")
            return None
        if raw is None:
            return None
        return json.loads(raw)

    def set_json(self, key: str, value, ttl_seconds: int) -> bool:
        try:
            sanitized_value = _sanitize_json_value(value)
            self.client.setex(key, ttl_seconds, json.dumps(sanitized_value, default=str))
            return True
        except RedisUnavailable:
            return False
        except Exception:
            logger.exception("redis_set_failed")
            return False

    def lpush_json(self, queue_name: str, payload: dict) -> bool:
        try:
            self.client.lpush(queue_name, json.dumps(_sanitize_json_value(payload), default=str))
            return True
        except RedisUnavailable:
            return False
        except Exception:
            logger.exception("redis_queue_push_failed")
            return False

    def rpop_json(self, queue_name: str) -> dict | None:
        try:
            raw = self.client.rpop(queue_name)
        except RedisUnavailable:
            return None
        except Exception:
            logger.exception("redis_queue_pop_failed")
            return None
        if raw is None:
            return None
        return json.loads(raw)


def _sanitize_json_value(value):
    if isinstance(value, str):
        return sanitize_for_llm(value, 20_000).text
    if isinstance(value, dict):
        return {key: _sanitize_json_value(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_sanitize_json_value(item) for item in value]
    return value


@lru_cache
def get_redis_client() -> RedisClient:
    return RedisClient(get_settings())


def enqueue_embedding_job(payload: dict) -> bool:
    client = get_redis_client()
    return client.lpush_json(client.settings.redis_queue_embedding, payload)


def enqueue_ai_processing_job(payload: dict) -> bool:
    client = get_redis_client()
    return client.lpush_json(client.settings.redis_queue_ai_processing, payload)
