from typing import Any

import redis
from loguru import logger

from app.config import get_settings

settings = get_settings()


redis_client = redis.Redis.from_url(
    settings.redis_url,
    decode_responses=True,
)


def check_redis_connection() -> bool:
    """
    Testa se a API consegue se comunicar com o Redis.

    Retorna True se o Redis responder ao PING.
    Retorna False se ocorrer qualquer erro.
    """
    try:
        response = redis_client.ping()

        if response is True:
            logger.success("Redis connection successful")
            return True

        logger.warning("Redis ping returned unexpected response: {}", response)
        return False

    except Exception:
        logger.exception("Redis connection failed")
        return False


def get_cache(key: str) -> str | None:
    """
    Busca um valor no Redis pela chave.
    """
    try:
        value = redis_client.get(key)

        logger.debug("Redis GET key={}", key)

        return value

    except Exception:
        logger.exception("Redis GET failed for key={}", key)
        return None


def set_cache(key: str, value: Any, expire_seconds: int | None = None) -> bool:
    """
    Salva um valor no Redis.

    expire_seconds:
    - None: chave não expira automaticamente.
    - int: chave expira após a quantidade de segundos informada.
    """
    try:
        redis_client.set(
            name=key,
            value=value,
            ex=expire_seconds,
        )

        logger.debug("Redis SET key={} expire_seconds={}", key, expire_seconds)

        return True

    except Exception:
        logger.exception("Redis SET failed for key={}", key)
        return False


def delete_cache(key: str) -> bool:
    """
    Remove uma chave do Redis.
    """
    try:
        deleted_count = redis_client.delete(key)

        logger.debug("Redis DELETE key={} deleted_count={}", key, deleted_count)

        return deleted_count > 0

    except Exception:
        logger.exception("Redis DELETE failed for key={}", key)
        return False