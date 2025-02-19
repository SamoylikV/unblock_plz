import logging
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, LabeledPrice, PreCheckoutQuery
from aiogram.enums import ParseMode
from config import AUTH_URL, PASSWORD, USERNAME, TG_TOKEN, PAYMENT_PROVIDER_TOKEN
from client_manager import ClientManager

client_manager = ClientManager(AUTH_URL, USERNAME, PASSWORD)
API_TOKEN = TG_TOKEN
logging.basicConfig(level=logging.INFO)
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

user_data = {}
active_messages = {}

tariff_mapping = {
    "tariff_1month": ("Доступ на 1 месяц", 250, 30),
    "tariff_5months": ("Доступ на 5 месяцев", 1000, 150),
    "tariff_12months": ("Доступ на 12 месяцев", 2000, 365)
}
tariff_keyboard = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text=f'{name} - {price}₽', callback_data=key)]
    for key, (name, price, _) in tariff_mapping.items()
])

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
    sent = await message.answer("🎛 Выберите тарифный план:", reply_markup=tariff_keyboard)
    add_active_message(message.from_user.id, sent)


@dp.callback_query(lambda callback: callback.data in tariff_mapping)
async def select_tariff(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    await clear_active_messages(user_id)

    tariff_name, price, days = tariff_mapping[callback.data]
    user_data[user_id] = {"tariff": tariff_name, "price": price, "days": days}

    invoice_keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=f"Заплатить {price}₽", pay=True)],
            [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_payment")]
        ]
    )

    invoice_msg = await bot.send_invoice(
        chat_id=user_id,
        title=tariff_name,
        description=f"Оплата {tariff_name}",
        payload=f"tariff_{user_id}",
        provider_token=PAYMENT_PROVIDER_TOKEN,
        currency="RUB",
        prices=[LabeledPrice(label=tariff_name, amount=price * 100)],
        start_parameter="pay",
        reply_markup=invoice_keyboard
    )
    add_active_message(user_id, invoice_msg)
    await callback.answer()


@dp.callback_query(lambda callback: callback.data == "cancel_payment")
async def cancel_payment(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    await clear_active_messages(user_id)
    if user_id in user_data:
        del user_data[user_id]
    sent = await callback.message.answer("🎛 Выберите тарифный план:", reply_markup=tariff_keyboard)
    add_active_message(callback.from_user.id, sent)
    await callback.answer()

@dp.pre_checkout_query()
async def checkout(pre_checkout_query: PreCheckoutQuery):
    await bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)

@dp.message(lambda message: message.successful_payment)
async def process_payment(message: Message):
    user_id = message.from_user.id
    await clear_active_messages(user_id)
    if user_id not in user_data:
        await message.answer("Ошибка: не найден тариф!")
        return
    try:
        client_manager.authenticate()
        days = user_data[user_id]["days"]
        email = message.from_user.username
        clients = client_manager.generate_clients(email, days)
        client_manager.add_clients(clients)
        key = client_manager.get_vless(email)
    except Exception as e:
        key = f"Ошибка генерации ключа: {e}"
    with open("instructions.html", "r", encoding="utf-8") as f:
        instructions = f.read()
    combined_text = f"{instructions}\n\n<b>Ваш ключ доступа:</b>\n<pre><code>{key}</code></pre>"
    sent = await message.answer(text=combined_text, parse_mode=ParseMode.HTML, disable_web_page_preview=True)
    add_active_message(user_id, sent)
    del user_data[user_id]

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
