import logging
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.utils import executor

# Telegram API Token
API_TOKEN = '6072615655:AAHQh3BVU3HNHd3p7vfvE3JsBzfHiG-hNMU'
CHANNEL_ID = '@precoinmarket_channel'

# Temporary storage for user data
user_data = {}

# Initialize bot and dispatcher
logging.basicConfig(level=logging.INFO)
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

# Step 1: Start Command
@dp.message_handler(commands=['start'])
async def start_command(message: types.Message):
    user_data[message.from_user.id] = {}
    await send_transport_options(message)

# Step 1.1: Helper to send transport options
async def send_transport_options(message):
    transport_kb = InlineKeyboardMarkup(row_width=2)
    transport_kb.add(
        InlineKeyboardButton("Автомобилями", callback_data="transport_auto"),
        InlineKeyboardButton("Вагонами", callback_data="transport_train")
    )
    await bot.send_message(
        message.from_user.id, 
        "Выберите способ транспортировки:", 
        reply_markup=transport_kb
    )

# Step 2: Transport Selection
@dp.callback_query_handler(lambda c: c.data.startswith('transport_'))
async def choose_transport(callback_query: CallbackQuery):
    transport = callback_query.data.split('_')[1]
    user_data[callback_query.from_user.id]['transport'] = "Автомобилями" if transport == 'auto' else "Вагонами"
    
    cargo_kb = InlineKeyboardMarkup(row_width=2)
    cargo_kb.add(*[
        InlineKeyboardButton(name, callback_data=f"cargo_{name}") for name in [
            "Песок", "Цемент М500", "Цемент М400", 
            "Щебень 5x10", "Щебень 5x20", "Щебень 10x20", 
            "Щебень 20x40", "Металлопрокат"
        ]
    ])
    await bot.edit_message_text(
        "Выберите груз:", 
        chat_id=callback_query.message.chat.id, 
        message_id=callback_query.message.message_id, 
        reply_markup=cargo_kb
    )

# Step 3: Cargo Selection
@dp.callback_query_handler(lambda c: c.data.startswith('cargo_'))
async def choose_cargo(callback_query: CallbackQuery):
    cargo = callback_query.data.split('_')[1]
    user_data[callback_query.from_user.id]['cargo'] = cargo
    
    if cargo == "Металлопрокат":
        type_kb = InlineKeyboardMarkup(row_width=2)
        type_kb.add(
            InlineKeyboardButton("Проволока", callback_data="type_Проволока"),
            InlineKeyboardButton("Металлопрокат", callback_data="type_Металлопрокат")
        )
        await bot.edit_message_text(
            "Выберите тип груза:", 
            chat_id=callback_query.message.chat.id, 
            message_id=callback_query.message.message_id, 
            reply_markup=type_kb
        )
    else:
        await send_sender_options(callback_query)

# Step 4: Type Selection (for Металлопрокат)
@dp.callback_query_handler(lambda c: c.data.startswith('type_'))
async def choose_type(callback_query: CallbackQuery):
    cargo_type = callback_query.data.split('_')[1]
    user_data[callback_query.from_user.id]['cargo_type'] = cargo_type
    await send_sender_options(callback_query)

# Helper to send sender options
async def send_sender_options(callback_query: CallbackQuery):
    if user_data[callback_query.from_user.id]['cargo'] == "Металлопрокат":
        sender_options = ["Викант", "АВ Металл Групп", "Парк Плюс"]
    else:
        sender_options = [
            "Кривой Рог Цемент", "Петриковский рыбхоз", 
            "ТОВ 'МКК №3'", "БОСС Технолайн", "СпецКарьер"
        ]

    sender_kb = InlineKeyboardMarkup(row_width=2)
    sender_kb.add(*[
        InlineKeyboardButton(name, callback_data=f"sender_{name}") for name in sender_options
    ])
    await bot.edit_message_text(
        "Выберите отправителя:", 
        chat_id=callback_query.message.chat.id, 
        message_id=callback_query.message.message_id, 
        reply_markup=sender_kb
    )

# Step 5: Sender Selection
@dp.callback_query_handler(lambda c: c.data.startswith('sender_'))
async def choose_sender(callback_query: CallbackQuery):
    sender = callback_query.data.split('_')[1]
    user_data[callback_query.from_user.id]['sender'] = sender
    
    if user_data[callback_query.from_user.id]['transport'] == "Автомобилями" and user_data[callback_query.from_user.id]['cargo'] != "Металлопрокат":
        quantity_kb = InlineKeyboardMarkup(row_width=3)
        quantity_kb.add(*[InlineKeyboardButton(str(i), callback_data=f"quantity_{i}") for i in range(1, 4)])
        await bot.edit_message_text(
            "Количество машин?", 
            chat_id=callback_query.message.chat.id, 
            message_id=callback_query.message.message_id, 
            reply_markup=quantity_kb
        )
    else:
        await send_status_options(callback_query)

# Step 6: Status Selection
@dp.callback_query_handler(lambda c: c.data.startswith('status_'))
async def choose_status(callback_query: CallbackQuery):
    status = callback_query.data.split('_')[1]
    status_mapping = {
        "unloaded": "Разгружено",
        "not_unloaded": "Не разгружено",
        "unspecified": "Не указано"
    }
    user_data[callback_query.from_user.id]['status'] = status_mapping[status]
    await confirm_order(callback_query)

# Step 7: Confirm Order
async def confirm_order(callback_query: CallbackQuery):
    data = user_data[callback_query.from_user.id]
    message = (
        f"Транспортировка: {data['transport']}\n"
        f"Груз: {data['cargo']}\n"
        f"Отправитель: {data['sender']}\n"
    )
    if 'cargo_type' in data:
        message += f"Тип груза: {data['cargo_type']}\n"
    if 'quantity' in data:
        message += f"Количество машин: {data['quantity']}\n"
    if 'status' in data:
        message += f"Статус разгрузки: {data['status']}\n"
    
    confirm_kb = InlineKeyboardMarkup(row_width=2)
    confirm_kb.add(
        InlineKeyboardButton("Подтвердить", callback_data="confirm"),
        InlineKeyboardButton("Отмена", callback_data="cancel")
    )
    await bot.edit_message_text(
        message, 
        chat_id=callback_query.message.chat.id, 
        message_id=callback_query.message.message_id, 
        reply_markup=confirm_kb
    )

# Step 8: Confirmation
@dp.callback_query_handler(lambda c: c.data == "confirm")
async def confirm_order(callback_query: CallbackQuery):
    data = user_data.pop(callback_query.from_user.id, {})
    message = (
        f"Новый заказ:\n"
        f"Транспортировка: {data['transport']}\n"
        f"Груз: {data['cargo']}\n"
        f"Отправитель: {data['sender']}\n"
    )
    if 'cargo_type' in data:
        message += f"Тип груза: {data['cargo_type']}\n"
    if 'quantity' in data:
        message += f"Количество машин: {data['quantity']}\n"
    if 'status' in data:
        message += f"Статус разгрузки: {data['status']}\n"
    
    await bot.send_message(CHANNEL_ID, message)
    await bot.send_message(callback_query.from_user.id, "Сообщение отправлено в канал!")
    await send_transport_options(callback_query.message)

# Step 9: Cancel Order
@dp.callback_query_handler(lambda c: c.data == "cancel")
async def cancel_order(callback_query: CallbackQuery):
    user_data.pop(callback_query.from_user.id, None)
    await bot.edit_message_text(
        "Заказ отменён. Начинаем заново.",
        chat_id=callback_query.message.chat.id,
        message_id=callback_query.message.message_id
    )
    await send_transport_options(callback_query.message)

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
