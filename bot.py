# bot.py
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.utils import executor

# Telegram токен
API_TOKEN = '6072615655:AAHQh3BVU3HNHd3p7vfvE3JsBzfHiG-hNMU'
CHANNEL_ID = '@bsc_ceh'

# Временное хранилище данных пользователей
user_data = {}

# Настройка логгирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Инициализация бота и диспетчера
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)
dp.middleware.setup(LoggingMiddleware())

# Шаг 1: Начало сценария
@dp.message_handler(commands=['start'])
async def start_handler(message: types.Message):
    user_data[message.from_user.id] = {}
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton("Сообщить о товаре", callback_data="scenario_1"))
    keyboard.add(InlineKeyboardButton("Товар в вагонах", callback_data="scenario_2"))
    await message.answer("Выберите следующий вариант:", reply_markup=keyboard)

# Шаг 2: Обработка сценария
@dp.callback_query_handler(lambda c: c.data.startswith('scenario'))
async def scenario_handler(callback_query: CallbackQuery):
    scenario = callback_query.data
    user_data[callback_query.from_user.id]['scenario'] = scenario
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(*[InlineKeyboardButton(name, callback_data=f"cargo_{name}") for name in [
        "Песок", "Цемент М500", "Цемент М400", "Щебень 5x10", "Щебень 5x20", "Щебень 10x20", "Щебень 20x40", "Металлопрокат"
    ]])
    await bot.send_message(callback_query.from_user.id, "Выберите тип или марку/фракцию груза:", reply_markup=keyboard)

# Шаг 3: Выбор отправителя
@dp.callback_query_handler(lambda c: c.data.startswith('cargo'))
async def cargo_handler(callback_query: CallbackQuery):
    cargo = callback_query.data.split('_')[1]
    user_data[callback_query.from_user.id]['cargo'] = cargo
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(*[InlineKeyboardButton(name, callback_data=f"sender_{name}") for name in [
        "Кривой рог цемент", "СпецКарьер", "Смарт Гранит", "Баловские пески", "Любимовский карьер", "Бородавский карьер", "ТОВ МКК №3", "Новатор"
    ]])
    await bot.send_message(callback_query.from_user.id, "Выберите товаро-отправителя:", reply_markup=keyboard)

# Шаг 4: Подтверждение
@dp.callback_query_handler(lambda c: c.data.startswith('sender'))
async def sender_handler(callback_query: CallbackQuery):
    sender = callback_query.data.split('_')[1]
    user_data[callback_query.from_user.id]['sender'] = sender
    
    # Формируем текст подтверждения
    data = user_data[callback_query.from_user.id]
    transport = "Автомобилем" if data['scenario'] == "scenario_1" else "Вагонами"
    message = (
        f"Подтвердите:\n"
        f"Транспортировка: {transport}\n"
        f"Груз: {data['cargo']}\n"
        f"Отправитель: {data['sender']}"
    )
    
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton("Подтвердить", callback_data="confirm"))
    keyboard.add(InlineKeyboardButton("Отмена", callback_data="cancel"))
    
    await bot.send_message(callback_query.from_user.id, message, reply_markup=keyboard)

# Шаг 5: Подтверждение и отправка в канал
@dp.callback_query_handler(lambda c: c.data == "confirm")
async def confirm_handler(callback_query: CallbackQuery):
    data = user_data.pop(callback_query.from_user.id, {})
    transport = "Автомобилем" if data['scenario'] == "scenario_1" else "Вагонами"
    message = (
        f"Новый заказ:\n"
        f"Транспортировка: {transport}\n"
        f"Груз: {data['cargo']}\n"
        f"Отправитель: {data['sender']}"
    )
    # Отправляем в канал
    await bot.send_message(CHANNEL_ID, message)
    await bot.send_message(callback_query.from_user.id, "Данные отправлены в канал!")

# Шаг 6: Обработка отмены
@dp.callback_query_handler(lambda c: c.data == "cancel")
async def cancel_handler(callback_query: CallbackQuery):
    user_data.pop(callback_query.from_user.id, None)
    await bot.send_message(callback_query.from_user.id, "Отменено.")

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
