import os

from aiogram import types
from aiogram.filters import Command
from aiogram.types import Message, InputFile, BufferedInputFile
from aiogram.enums import ParseMode
from config import PROVIDER


def register_handlers(dp, bot, client_manager, redis_manager):
    active_messages = {}

    async def clear_active_messages(user_id: int):
        if user_id in active_messages:
            for msg_id in active_messages[user_id]:
                try:
                    await bot.delete_message(user_id, msg_id)
                except Exception:
                    pass
            del active_messages[user_id]

    def add_active_message(user_id: int, msg: Message):
        if user_id not in active_messages:
            active_messages[user_id] = []
        active_messages[user_id].append(msg.message_id)

    @dp.message(Command("start"))
    async def cmd_start(message: Message):
        await clear_active_messages(message.from_user.id)
        user_id = message.from_user.id
        email = message.from_user.username
        days = 30

        try:
            if PROVIDER == "MARZBAN":
                clients = client_manager.generate_clients(email, days)
                await client_manager.add_clients(clients)
                key = await client_manager.get_vless(username=email)
            else:
                client_manager.authenticate()
                clients = client_manager.generate_clients(email, days)
                client_manager.add_clients(clients)
                key = client_manager.get_vless(email)
            await redis_manager.save_user_data(user_id, email, key, days)
        except Exception as e:
            key = str(e)

        with open("instructions.html", "r", encoding="utf-8") as f:
            instructions = f.read()
        flag = False
        if key[-1] == "9" and key[0] == "C" and key[7] == "e":
            combined_text = "У вас уже есть ключ доступа"
            flag = True
        else:
            combined_text = f"<pre><code>{key}</code></pre>"
        if not flag:
            sent = await message.answer(text=instructions, parse_mode=ParseMode.HTML, disable_web_page_preview=True)
            add_active_message(user_id, sent)
        sent = await message.answer(text=combined_text, parse_mode=ParseMode.HTML, disable_web_page_preview=True)
        add_active_message(user_id, sent)
        # if not flag:
        #     qr = client_manager.generate_qr(key)
        #     try:
        #         with open(qr, "rb") as file:
        #             file_data = file.read()
        #         input_file = BufferedInputFile(file_data, filename="qr_code.png")
        #         sent = await message.answer_photo(input_file)
        #         add_active_message(user_id, sent)
        #     finally:
        #         if os.path.exists(qr):
        #             os.remove(qr)
