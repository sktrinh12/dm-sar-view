import redis
from os import getenv

redis_conn = redis.Redis(
    host=getenv("REDIS_HOST", "127.0.0.1"),
    port=int(getenv("REDIS_PORT", 6379)),
    password=getenv("REDIS_PASSWD"),
)
