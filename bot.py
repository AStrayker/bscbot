import logging
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils import executor

# Укажите ваш токен бота и ID канала
BOT_TOKEN = "6072615655:AAHQh3BVU3HNHd3p7vfvE3JsBzfHiG-hNMU"
CHANNEL_ID = "@precoinmarket_channel"

# Логирование
logging.basicConfig(level=logging.INFO)

# Инициализация бота и диспетчера
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)
dp.middleware.setup(LoggingMiddleware())

# Глобальные переменные для хранения данных
user_data = {}

# Кнопки для основного меню
transport_menu = ReplyKeyboardMarkup(resize_keyboard=True).add(
    KeyboardButton("Автомобилем"),
    KeyboardButton("Вагонами"),
)

# Кнопки для выбора груза
cargo_menu = ReplyKeyboardMarkup(resize_keyboard=True).add(
    KeyboardButton("Песок"),
    KeyboardButton("Цемент 400"),
    KeyboardButton("Цемент 500"),
    KeyboardButton("Щебень 5x10"),
    KeyboardButton("Металлопрокат"),
)

# Кнопки для отправителей
sender_menu = ReplyKeyboardMarkup(resize_keyboard=True).add(
    KeyboardButton("Викант"),
    KeyboardButton("Вартис"),
    KeyboardButton("ПаркПлюс"),
)

# Кнопки для статуса разгрузки
status_menu = ReplyKeyboardMarkup(resize_keyboard=True).add(
    KeyboardButton("Разгружен"),
    KeyboardButton("Не разгружен"),
    KeyboardButton("Не указан"),
)

# Кнопки для подтверждения
confirm_menu = ReplyKeyboardMarkup(resize_keyboard=True).add(
    KeyboardButton("Отправить"),
    KeyboardButton("Отменить"),
)

@dp.message_handler(commands=["start"])
async def start_handler(message: types.Message):
    """Начало работы бота."""
    user_data[message.from_user.id] = {}
    await message.answer(
        "Выберите способ транспортировки:", reply_markup=transport_menu
    )

@dp.message_handler(lambda message: message.text in ["Автомобилем", "Вагонами"])
async def transport_handler(message: types.Message):
    """Выбор способа транспортировки."""
    user_data[message.from_user.id]["transport"] = message.text
    if message.text == "Автомобилем":
        await message.answer("Выберите груз:", reply_markup=cargo_menu)
    else:
        await message.answer("Выберите груз:", reply_markup=cargo_menu)

@dp.message_handler(lambda message: message.text in ["Песок", "Цемент 400", "Цемент 500", "Щебень 5x10", "Металлопрокат"])
async def cargo_handler(message: types.Message):
    """Выбор груза."""
    user_data[message.from_user.id]["cargo"] = message.text
    if message.text == "Металлопрокат":
        await message.answer("Выберите тип:", reply_markup=ReplyKeyboardMarkup(resize_keyboard=True).add(
            KeyboardButton("Проволока"),
            KeyboardButton("Металлопрокат"),
        ))
    else:
        await message.answer("Выберите отправителя:", reply_markup=sender_menu)

@dp.message_handler(lambda message: message.text in ["Викант", "Вартис", "ПаркПлюс"])
async def sender_handler(message: types.Message):
    """Выбор отправителя."""
    user_data[message.from_user.id]["sender"] = message.text
    await message.answer("Укажите количество машин (например: 4):")

@dp.message_handler(lambda message: message.text.isdigit())
async def quantity_handler(message: types.Message):
    """Указание количества машин."""
    user_data[message.from_user.id]["quantity"] = message.text
    await message.answer(
        f"Транспортировка: {user_data[message.from_user.id]['transport']}\n"
        f"Груз: {user_data[message.from_user.id]['cargo']}\n"
        f"Отправитель: {user_data[message.from_user.id]['sender']}\n"
        f"Количество машин: {user_data[message.from_user.id]['quantity']}\n"
        f"Подтвердите отправку:",
        reply_markup=confirm_menu,
    )

@dp.message_handler(lambda message: message.text in ["Отправить", "Отменить"])
async def confirm_handler(message: types.Message):
    """Подтверждение или отмена."""
    if message.text == "Отправить":
        data = user_data.get(message.from_user.id, {})
        await bot.send_message(
            CHANNEL_ID,
            f"Транспортировка: {data.get('transport')}\n"
            f"Груз: {data.get('cargo')}\n"
            f"Отправитель: {data.get('sender')}\n"
            f"Количество машин: {data.get('quantity')}",
        )
        await message.answer("Данные успешно отправлены в канал!")
    else:
        await message.answer("Отправка отменена.")
    user_data.pop(message.from_user.id, None)
    await start_handler(message)

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
# файл: telegram_transport_bot.py

import logging
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils import executor

# Укажите ваш токен бота и ID канала
BOT_TOKEN = "your_bot_token_here"
CHANNEL_ID = "@your_channel_id"

# Логирование
logging.basicConfig(level=logging.INFO)

# Инициализация бота и диспетчера
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)
dp.middleware.setup(LoggingMiddleware())

# Глобальные переменные для хранения данных
user_data = {}

# Кнопки для основного меню
transport_menu = ReplyKeyboardMarkup(resize_keyboard=True).add(
    KeyboardButton("Автомобилем"),
    KeyboardButton("Вагонами"),
)

# Кнопки для выбора груза
cargo_menu = ReplyKeyboardMarkup(resize_keyboard=True).add(
    KeyboardButton("Песок"),
    KeyboardButton("Цемент 400"),
    KeyboardButton("Цемент 500"),
    KeyboardButton("Щебень 5x10"),
    KeyboardButton("Металлопрокат"),
)

# Кнопки для отправителей
sender_menu = ReplyKeyboardMarkup(resize_keyboard=True).add(
    KeyboardButton("Викант"),
    KeyboardButton("Вартис"),
    KeyboardButton("ПаркПлюс"),
)

# Кнопки для статуса разгрузки
status_menu = ReplyKeyboardMarkup(resize_keyboard=True).add(
    KeyboardButton("Разгружен"),
    KeyboardButton("Не разгружен"),
    KeyboardButton("Не указан"),
)

# Кнопки для подтверждения
confirm_menu = ReplyKeyboardMarkup(resize_keyboard=True).add(
    KeyboardButton("Отправить"),
    KeyboardButton("Отменить"),
)

@dp.message_handler(commands=["start"])
async def start_handler(message: types.Message):
    """Начало работы бота."""
    user_data[message.from_user.id] = {}
    await message.answer(
        "Выберите способ транспортировки:", reply_markup=transport_menu
    )

@dp.message_handler(lambda message: message.text in ["Автомобилем", "Вагонами"])
async def transport_handler(message: types.Message):
    """Выбор способа транспортировки."""
    user_data[message.from_user.id]["transport"] = message.text
    if message.text == "Автомобилем":
        await message.answer("Выберите груз:", reply_markup=cargo_menu)
    else:
        await message.answer("Выберите груз:", reply_markup=cargo_menu)

@dp.message_handler(lambda message: message.text in ["Песок", "Цемент 400", "Цемент 500", "Щебень 5x10", "Металлопрокат"])
async def cargo_handler(message: types.Message):
    """Выбор груза."""
    user_data[message.from_user.id]["cargo"] = message.text
    if message.text == "Металлопрокат":
        await message.answer("Выберите тип:", reply_markup=ReplyKeyboardMarkup(resize_keyboard=True).add(
            KeyboardButton("Проволока"),
            KeyboardButton("Металлопрокат"),
        ))
    else:
        await message.answer("Выберите отправителя:", reply_markup=sender_menu)

@dp.message_handler(lambda message: message.text in ["Викант", "Вартис", "ПаркПлюс"])
async def sender_handler(message: types.Message):
    """Выбор отправителя."""
    user_data[message.from_user.id]["sender"] = message.text
    await message.answer("Укажите количество машин (например: 4):")

@dp.message_handler(lambda message: message.text.isdigit())
async def quantity_handler(message: types.Message):
    """Указание количества машин."""
    user_data[message.from_user.id]["quantity"] = message.text
    await message.answer(
        f"Транспортировка: {user_data[message.from_user.id]['transport']}\n"
        f"Груз: {user_data[message.from_user.id]['cargo']}\n"
        f"Отправитель: {user_data[message.from_user.id]['sender']}\n"
        f"Количество машин: {user_data[message.from_user.id]['quantity']}\n"
        f"Подтвердите отправку:",
        reply_markup=confirm_menu,
    )

@dp.message_handler(lambda message: message.text in ["Отправить", "Отменить"])
async def confirm_handler(message: types.Message):
    """Подтверждение или отмена."""
    if message.text == "Отправить":
        data = user_data.get(message.from_user.id, {})
        await bot.send_message(
            CHANNEL_ID,
            f"Транспортировка: {data.get('transport')}\n"
            f"Груз: {data.get('cargo')}\n"
            f"Отправитель: {data.get('sender')}\n"
            f"Количество машин: {data.get('quantity')}",
        )
        await message.answer("Данные успешно отправлены в канал!")
    else:
        await message.answer("Отправка отменена.")
    user_data.pop(message.from_user.id, None)
    await start_handler(message)

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
# файл: telegram_transport_bot.py

import logging
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils import executor

# Укажите ваш токен бота и ID канала
BOT_TOKEN = "your_bot_token_here"
CHANNEL_ID = "@your_channel_id"

# Логирование
logging.basicConfig(level=logging.INFO)

# Инициализация бота и диспетчера
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)
dp.middleware.setup(LoggingMiddleware())

# Глобальные переменные для хранения данных
user_data = {}

# Кнопки для основного меню
transport_menu = ReplyKeyboardMarkup(resize_keyboard=True).add(
    KeyboardButton("Автомобилем"),
    KeyboardButton("Вагонами"),
)

# Кнопки для выбора груза
cargo_menu = ReplyKeyboardMarkup(resize_keyboard=True).add(
    KeyboardButton("Песок"),
    KeyboardButton("Цемент 400"),
    KeyboardButton("Цемент 500"),
    KeyboardButton("Щебень 5x10"),
    KeyboardButton("Металлопрокат"),
)

# Кнопки для отправителей
sender_menu = ReplyKeyboardMarkup(resize_keyboard=True).add(
    KeyboardButton("Викант"),
    KeyboardButton("Вартис"),
    KeyboardButton("ПаркПлюс"),
)

# Кнопки для статуса разгрузки
status_menu = ReplyKeyboardMarkup(resize_keyboard=True).add(
    KeyboardButton("Разгружен"),
    KeyboardButton("Не разгружен"),
    KeyboardButton("Не указан"),
)

# Кнопки для подтверждения
confirm_menu = ReplyKeyboardMarkup(resize_keyboard=True).add(
    KeyboardButton("Отправить"),
    KeyboardButton("Отменить"),
)

@dp.message_handler(commands=["start"])
async def start_handler(message: types.Message):
    """Начало работы бота."""
    user_data[message.from_user.id] = {}
    await message.answer(
        "Выберите способ транспортировки:", reply_markup=transport_menu
    )

@dp.message_handler(lambda message: message.text in ["Автомобилем", "Вагонами"])
async def transport_handler(message: types.Message):
    """Выбор способа транспортировки."""
    user_data[message.from_user.id]["transport"] = message.text
    if message.text == "Автомобилем":
        await message.answer("Выберите груз:", reply_markup=cargo_menu)
    else:
        await message.answer("Выберите груз:", reply_markup=cargo_menu)

@dp.message_handler(lambda message: message.text in ["Песок", "Цемент 400", "Цемент 500", "Щебень 5x10", "Металлопрокат"])
async def cargo_handler(message: types.Message):
    """Выбор груза."""
    user_data[message.from_user.id]["cargo"] = message.text
    if message.text == "Металлопрокат":
        await message.answer("Выберите тип:", reply_markup=ReplyKeyboardMarkup(resize_keyboard=True).add(
            KeyboardButton("Проволока"),
            KeyboardButton("Металлопрокат"),
        ))
    else:
        await message.answer("Выберите отправителя:", reply_markup=sender_menu)

@dp.message_handler(lambda message: message.text in ["Викант", "Вартис", "ПаркПлюс"])
async def sender_handler(message: types.Message):
    """Выбор отправителя."""
    user_data[message.from_user.id]["sender"] = message.text
    await message.answer("Укажите количество машин (например: 4):")

@dp.message_handler(lambda message: message.text.isdigit())
async def quantity_handler(message: types.Message):
    """Указание количества машин."""
    user_data[message.from_user.id]["quantity"] = message.text
    await message.answer(
        f"Транспортировка: {user_data[message.from_user.id]['transport']}\n"
        f"Груз: {user_data[message.from_user.id]['cargo']}\n"
        f"Отправитель: {user_data[message.from_user.id]['sender']}\n"
        f"Количество машин: {user_data[message.from_user.id]['quantity']}\n"
        f"Подтвердите отправку:",
        reply_markup=confirm_menu,
    )

@dp.message_handler(lambda message: message.text in ["Отправить", "Отменить"])
async def confirm_handler(message: types.Message):
    """Подтверждение или отмена."""
    if message.text == "Отправить":
        data = user_data.get(message.from_user.id, {})
        await bot.send_message(
            CHANNEL_ID,
            f"Транспортировка: {data.get('transport')}\n"
            f"Груз: {data.get('cargo')}\n"
            f"Отправитель: {data.get('sender')}\n"
            f"Количество машин: {data.get('quantity')}",
        )
        await message.answer("Данные успешно отправлены в канал!")
    else:
        await message.answer("Отправка отменена.")
    user_data.pop(message.from_user.id, None)
    await start_handler(message)

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
