import logging

from redis.asyncio import Redis

from app.config import settings

logger = logging.getLogger(__name__)

_redis_client = None

async def get_redis_client() -> Redis:
    """Возвращает асинхронный клиент Redis (один экземпляр на всё приложение)."""
    global _redis_client
    if _redis_client is None:
        _redis_client = Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=getattr(settings, "REDIS_DB", 0),
            decode_responses=True,
            socket_connect_timeout=2
        )
        logger.info(f"Redis клиент создан: {settings.REDIS_HOST}:{settings.REDIS_PORT}")
    return _redis_client