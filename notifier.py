import asyncio
from datetime import datetime, timedelta
from aiogram import Bot
from redis_manager import RedisManager

class Notifier:
    def __init__(self, redis_manager: RedisManager, bot: Bot):
        self.redis_manager = redis_manager
        self.bot = bot

    async def check_subscriptions(self):
        while True:
            users = await self.redis_manager.get_all_users()
            now = datetime.utcnow()

            for user_id, data in users:
                if b'expires_at' not in data:
                    continue
                expires_at_str = data[b'expires_at'].decode('utf-8')
                try:
                    expires_at = datetime.strptime(expires_at_str, "%Y-%m-%d %H:%M:%S")
                except ValueError as e:
                    continue

                time_left = expires_at - now

                if timedelta(days=2) >= time_left > timedelta(days=1):
                    await self.send_notification(user_id, "⚠️ Ваша подписка истекает через 2 дня!")
                elif timedelta(days=1) >= time_left > timedelta(hours=1):
                    await self.send_notification(user_id, "⚠️ Ваша подписка истекает через 1 день!")
                elif timedelta(hours=1) >= time_left > timedelta(minutes=0):
                    await self.send_notification(user_id, "⚠️ Ваша подписка истекает через 1 час!")
                elif time_left <= timedelta(seconds=0):
                    await self.send_notification(user_id, "❌ Ваша подписка закончилась!")
                    await self.redis_manager.delete_user_data(user_id)

            await asyncio.sleep(3600)

    async def send_notification(self, user_id, text):
        try:
            await self.bot.send_message(user_id, text)
        except Exception as e:
            print(f"Ошибка при отправке сообщения пользователю {user_id}: {e}")
