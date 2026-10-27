from redis.asyncio import Redis

from data import config


def create_redis() -> Redis:
    return Redis.from_url(config.REDIS_URL, decode_responses=True)
