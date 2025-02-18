import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.enums import ParseMode
from config import AUTH_URL, PASSWORD, USERNAME, TG_TOKEN
from client_manager import ClientManager

client_manager = ClientManager(AUTH_URL, USERNAME, PASSWORD)
client_manager.authenticate()

API_TOKEN = TG_TOKEN

logging.basicConfig(level=logging.INFO)

bot = Bot(token=API_TOKEN)
dp = Dispatcher()


@dp.message(Command("start"))
async def cmd_start(message: Message):
    try:
        clients = client_manager.generate_clients(message.from_user.username)
        client_manager.add_clients(clients)
        key = client_manager.get_vless(message.from_user.username)
    except Exception as e:
        key = "ERROR"


    instructions = """
<b>📲 Инструкции по подключению VPN для разных устройств</b>
------------------------------
<b>▶️ Android:</b>
1. Скачайте приложение <a href="https://play.google.com/store/apps/details?id=app.hiddify.com">Hiddify-next (Google Play)</a> или <a href="https://github.com/hiddify/hiddify-next/releases/download/v1.5.2/Hiddify-Android-universal.apk">APK-версию</a>
2. Добавьте профиль через «Новый профиль → Добавить из буфера обмена»
------------------------------
<b>▶️ iOS:</b>
1. Установите <a href="https://apps.apple.com/us/app/streisand/id6450534064">Streisend</a>
2. Для импорта профиля нажмите + → Добавить из буфера обмена
------------------------------
<b>▶️ macOS:</b>
🔸 M1/M2: 
• Рекомендуем <a href="https://apps.apple.com/am/app/streisand/id6450534064">Streisand</a>
------------------------------
<b>▶️ Windows:</b>
1. Установите <a href="https://github.com/hiddify/hiddify-next/releases/download/v1.5.2/Hiddify-Windows-Setup-x64.exe">Hiddify-next</a>
2. Добавьте профиль через интерфейс приложения
<i>Альтернатива: <a href="https://telegra.ph/Alternativnoe-prilozhenie-dlya-Windows--FlClash-10-09">FlClash</a></i>
------------------------------
<b>▶️ Linux:</b>
1. Скачайте <a href="https://github.com/hiddify/hiddify-next/releases/latest/download/Hiddify-Linux-x64.AppImage">Hiddify</a>
2. Запустите и добавьте профиль
"""
    await message.answer(text=instructions, parse_mode=ParseMode.HTML, disable_web_page_preview=True)
    await message.answer(text=f"<pre><code>{key}</code></pre>", parse_mode=ParseMode.HTML)


async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())