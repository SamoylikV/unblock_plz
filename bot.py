import asyncio
import logging
from aiogram import Bot, Dispatcher
from config import TG_TOKEN, REDIS_URL, PROVIDER
from redis_manager import RedisManager
from notifier import Notifier
from handlers import register_handlers
from client_manager_3x import ClientManager
from client_manager_marzban import MarzbanClientManager

logging.basicConfig(level=logging.INFO)

bot = Bot(token=TG_TOKEN)
dp = Dispatcher()
if PROVIDER == "MARZBAN":
    client_manager = MarzbanClientManager()
else:
    client_manager = ClientManager()

redis_manager = RedisManager(REDIS_URL)


async def main():
    await redis_manager.connect()
    register_handlers(dp, bot, client_manager, redis_manager)

    notifier = Notifier(redis_manager, bot)
    asyncio.create_task(notifier.check_subscriptions())

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
