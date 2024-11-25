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
    transport_kb = InlineKeyboardMarkup(row_width=2)
    transport_kb.add(
        InlineKeyboardButton("Автомобилями", callback_data="transport_auto"),
        InlineKeyboardButton("Вагонами", callback_data="transport_train")
    )
    await message.answer("Выберите способ транспортировки:", reply_markup=transport_kb)

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
    await bot.send_message(callback_query.from_user.id, "Выберите груз:", reply_markup=cargo_kb)

# Step 3: Cargo Selection
@dp.callback_query_handler(lambda c: c.data.startswith('cargo_'))
async def choose_cargo(callback_query: CallbackQuery):
    cargo = callback_query.data.split('_')[1]
    user_data[callback_query.from_user.id]['cargo'] = cargo
    
    if cargo in ["Проволока", "Металлопрокат"]:
        sender_kb = InlineKeyboardMarkup(row_width=2)
        sender_kb.add(*[
            InlineKeyboardButton(name, callback_data=f"sender_{name}") for name in ["Викант", "АВ Металл Групп", "Парк Плюс"]
        ])
        await bot.send_message(callback_query.from_user.id, "Выберите отправителя:", reply_markup=sender_kb)
    else:
        sender_kb = InlineKeyboardMarkup(row_width=2)
        sender_kb.add(*[
            InlineKeyboardButton(name, callback_data=f"sender_{name}") for name in [
                "Кривой Рог Цемент", "Петриковский рыбхоз", "ТОВ 'МКК №3'", 
                "БОСС Технолайн", "СпецКарьер"
            ]
        ])
        await bot.send_message(callback_query.from_user.id, "Выберите отправителя:", reply_markup=sender_kb)

# Step 4: Sender Selection
@dp.callback_query_handler(lambda c: c.data.startswith('sender_'))
async def choose_sender(callback_query: CallbackQuery):
    sender = callback_query.data.split('_')[1]
    user_data[callback_query.from_user.id]['sender'] = sender
    
    if user_data[callback_query.from_user.id]['transport'] == "Автомобилями":
        quantity_kb = InlineKeyboardMarkup(row_width=3)
        quantity_kb.add(*[InlineKeyboardButton(str(i), callback_data=f"quantity_{i}") for i in range(1, 4)])
        await bot.send_message(callback_query.from_user.id, "Количество машин?", reply_markup=quantity_kb)
    else:
        status_kb = InlineKeyboardMarkup(row_width=2)
        status_kb.add(
            InlineKeyboardButton("Разгружено", callback_data="status_unloaded"),
            InlineKeyboardButton("Не разгружено", callback_data="status_not_unloaded"),
            InlineKeyboardButton("Не указано", callback_data="status_unspecified")
        )
        await bot.send_message(callback_query.from_user.id, "Выберите статус разгрузки:", reply_markup=status_kb)

# Step 5: Quantity Selection
@dp.callback_query_handler(lambda c: c.data.startswith('quantity_'))
async def choose_quantity(callback_query: CallbackQuery):
    quantity = callback_query.data.split('_')[1]
    user_data[callback_query.from_user.id]['quantity'] = quantity
    await confirm_order(callback_query)

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
    if 'quantity' in data:
        message += f"Количество машин: {data['quantity']}\n"
    if 'status' in data:
        message += f"Статус разгрузки: {data['status']}\n"
    
    confirm_kb = InlineKeyboardMarkup(row_width=2)
    confirm_kb.add(
        InlineKeyboardButton("Подтвердить", callback_data="confirm"),
        InlineKeyboardButton("Отмена", callback_data="cancel")
    )
    await bot.send_message(callback_query.from_user.id, message, reply_markup=confirm_kb)

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
    if 'quantity' in data:
        message += f"Количество машин: {data['quantity']}\n"
    if 'status' in data:
        message += f"Статус разгрузки: {data['status']}\n"
    
    await bot.send_message(CHANNEL_ID, message)
    await bot.send_message(callback_query.from_user.id, "Сообщение отправлено в канал!")

# Step 9: Cancel Order
@dp.callback_query_handler(lambda c: c.data == "cancel")
async def cancel_order(callback_query: CallbackQuery):
    user_data.pop(callback_query.from_user.id, None)
    await bot.send_message(callback_query.from_user.id, "Заказ отменён.")

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
