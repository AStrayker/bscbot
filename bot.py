# bot.py
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.utils import executor

# Telegram токен
API_TOKEN = '6072615655:AAHQh3BVU3HNHd3p7vfvE3JsBzfHiG-hNMU'
CHANNEL_ID = '@precoinmarket_channel'

# Временное хранилище данных пользователей
user_data = {}

# Настройка логгирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Инициализация бота и диспетчера
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)
dp.middleware.setup(LoggingMiddleware())

# Шаг 1: Выбор способа транспортировки
@dp.message_handler(commands=['start'])
async def start_handler(message: types.Message):
    user_data.pop(message.from_user.id, None)  # Очистка предыдущих данных
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton("Автомобили", callback_data="transport_auto"))
    keyboard.add(InlineKeyboardButton("Вагоны", callback_data="transport_wagon"))
    await message.answer("Выберите способ транспортировки:", reply_markup=keyboard)

# Шаг 2: Выбор груза
@dp.callback_query_handler(lambda c: c.data.startswith('transport'))
async def transport_handler(callback_query: CallbackQuery):
    transport = callback_query.data.split('_')[1]
    user_data[callback_query.from_user.id] = {'transport': transport}
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(*[InlineKeyboardButton(name, callback_data=f"cargo_{name}") for name in [
        "Песок", "Цемент М500", "Цемент М400", "Щебень 5x10", "Щебень 5x20", "Щебень 10x20", "Щебень 20x40", "Металлопрокат"
    ]])
    await callback_query.message.edit_text("Выберите груз:", reply_markup=keyboard)

# Шаг 2.1: Подтипы для металлопроката
@dp.callback_query_handler(lambda c: c.data == 'cargo_Металлопрокат')
async def metal_type_handler(callback_query: CallbackQuery):
    user_data[callback_query.from_user.id]['cargo'] = "Металлопрокат"
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton("Проволока", callback_data="metal_type_Проволока"),
        InlineKeyboardButton("Металлопрокат", callback_data="metal_type_Металлопрокат")
    )
    await callback_query.message.edit_text("Выберите тип груза:", reply_markup=keyboard)

@dp.callback_query_handler(lambda c: c.data.startswith('metal_type'))
async def metal_subtype_handler(callback_query: CallbackQuery):
    subtype = callback_query.data.split('_')[1]
    user_data[callback_query.from_user.id]['subtype'] = subtype
    await choose_sender(callback_query)

# Шаг 3: Выбор отправителя
@dp.callback_query_handler(lambda c: c.data.startswith('cargo'))
async def cargo_handler(callback_query: CallbackQuery):
    cargo = callback_query.data.split('_')[1]
    user_data[callback_query.from_user.id]['cargo'] = cargo
    await choose_sender(callback_query)

async def choose_sender(callback_query: CallbackQuery):
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(*[InlineKeyboardButton(name, callback_data=f"sender_{name}") for name in [
        "Кривой Рог Цемент", "Петриковский Рыбхоз", "ТОВ МКК №3", "БДСС Технологии", "СпецКарьер"
    ]])
    await callback_query.message.edit_text("Выберите отправителя:", reply_markup=keyboard)

# Шаг 4: Количество машин (только для автомобилей)
@dp.callback_query_handler(lambda c: c.data.startswith('sender'))
async def sender_handler(callback_query: CallbackQuery):
    sender = callback_query.data.split('_')[1]
    user_data[callback_query.from_user.id]['sender'] = sender

    if user_data[callback_query.from_user.id]['transport'] == 'auto':
        keyboard = InlineKeyboardMarkup(row_width=3)
        keyboard.add(
            InlineKeyboardButton("1", callback_data="quantity_1"),
            InlineKeyboardButton("2", callback_data="quantity_2"),
            InlineKeyboardButton("3", callback_data="quantity_3")
        )
        await callback_query.message.edit_text("Укажите количество машин:", reply_markup=keyboard)
    else:
        await choose_status(callback_query)

@dp.callback_query_handler(lambda c: c.data.startswith('quantity'))
async def quantity_handler(callback_query: CallbackQuery):
    quantity = callback_query.data.split('_')[1]
    user_data[callback_query.from_user.id]['quantity'] = quantity
    await choose_status(callback_query)

# Шаг 5: Выбор статуса
async def choose_status(callback_query: CallbackQuery):
    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        InlineKeyboardButton("Разгружено", callback_data="status_Разгружено"),
        InlineKeyboardButton("Не разгружено", callback_data="status_Не разгружено"),
        InlineKeyboardButton("Не указано", callback_data="status_Не указано")
    )
    await callback_query.message.edit_text("Выберите статус:", reply_markup=keyboard)

@dp.callback_query_handler(lambda c: c.data.startswith('status'))
async def status_handler(callback_query: CallbackQuery):
    status = callback_query.data.split('_')[1]
    user_data[callback_query.from_user.id]['status'] = status
    await confirm_data(callback_query)

# Шаг 6: Подтверждение и отправка
async def confirm_data(callback_query: CallbackQuery):
    data = user_data[callback_query.from_user.id]
    transport = "Автомобили" if data['transport'] == "auto" else "Вагоны"
    cargo = f"{data['cargo']} ({data.get('subtype', '')})"
    quantity = data.get('quantity', "Не указано")
    message = (
        f"Формирование сообщения:\n"
        f"Транспортировка: {transport}\n"
        f"Груз: {cargo}\n"
        f"Отправитель: {data['sender']}\n"
        f"Количество: {quantity}\n"
        f"Статус: {data['status']}"
    )
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton("Подтвердить", callback_data="confirm"))
    keyboard.add(InlineKeyboardButton("Отмена", callback_data="cancel"))
    await callback_query.message.edit_text(message, reply_markup=keyboard)

@dp.callback_query_handler(lambda c: c.data == "confirm")
async def confirm_handler(callback_query: CallbackQuery):
    data = user_data.pop(callback_query.from_user.id, {})
    transport = "Автомобили" if data['transport'] == "auto" else "Вагоны"
    cargo = f"{data['cargo']} ({data.get('subtype', '')})"
    quantity = data.get('quantity', "Не указано")
    message = (
        f"Транспортировка: {transport}\n"
        f"Груз: {cargo}\n"
        f"Отправитель: {data['sender']}\n"
        f"Количество: {quantity}\n"
        f"Статус: {data['status']}"
    )
    await bot.send_message(CHANNEL_ID, message)
    await callback_query.message.edit_text("Данные успешно отправлены в канал!")
    await start_handler(callback_query.message)

@dp.callback_query_handler(lambda c: c.data == "cancel")
async def cancel_handler(callback_query: CallbackQuery):
    user_data.pop(callback_query.from_user.id, None)
    await callback_query.message.edit_text("Операция отменена. Возвращаюсь к началу...")
    await start_handler(callback_query.message)

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
