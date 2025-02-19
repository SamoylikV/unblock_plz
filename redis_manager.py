import redis.asyncio as redis
from datetime import datetime, timedelta

class RedisManager:
    def __init__(self, redis_url):
        self.redis_url = redis_url
        self.redis = None

    async def connect(self):
        self.redis = redis.from_url(self.redis_url)

    async def save_user_data(self, user_id, email, key, days):
        expires_at = (datetime.utcnow() + timedelta(days=days)).strftime("%Y-%m-%d %H:%M:%S")
        data = {
            "email": email,
            "key": key,
            "expires_at": expires_at
        }
        await self.redis.hset(f"user:{user_id}", mapping=data)

    async def get_user_data(self, user_id):
        return await self.redis.hgetall(f"user:{user_id}")

    async def delete_user_data(self, user_id):
        await self.redis.delete(f"user:{user_id}")

    async def get_all_users(self):
        keys = await self.redis.keys("user:*")
        users = []
        for key in keys:
            key_type = await self.redis.type(key)
            if key_type != 'hash':
                continue
            key_str = key.decode('utf-8')
            _, user_id = key_str.split(':', 1)
            user_data = await self.get_user_data(user_id)
            users.append((int(user_id), user_data))
        return users

