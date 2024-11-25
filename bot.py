# bot.py
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.utils import executor
from aiogram.dispatcher.filters import Text

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

# Начало сценария
@dp.message_handler(commands=['start'])
async def start_handler(message: types.Message):
    user_data[message.from_user.id] = {}
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton("Сообщить о товаре", callback_data="scenario_1"))
    keyboard.add(InlineKeyboardButton("Товар в вагонах", callback_data="scenario_2"))
    await message.answer("Выберите следующий вариант:", reply_markup=keyboard)

# Обработка сценария
@dp.callback_query_handler(lambda c: c.data.startswith('scenario'))
async def scenario_handler(callback_query: CallbackQuery):
    scenario = callback_query.data
    user_data[callback_query.from_user.id]['scenario'] = scenario
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(*[InlineKeyboardButton(name, callback_data=f"cargo_{name}") for name in [
        "Цемент М400", "Цемент М500", "Щебень 5x10", "Щебень 5x20", "Щебень 10x20", "Щебень 20x40", "Проволока", "Металлопрокат"
    ]])
    await bot.send_message(callback_query.from_user.id, "Выберите тип или марку/фракцию груза:", reply_markup=keyboard)

# Выбор груза
@dp.callback_query_handler(lambda c: c.data.startswith('cargo'))
async def cargo_handler(callback_query: CallbackQuery):
    cargo = callback_query.data.split('_')[1]
    user_data[callback_query.from_user.id]['cargo'] = cargo

    # Проверка, нужно ли выбрать отправителя или указать текстом
    if cargo in ["Проволока", "Металлопрокат"]:
        keyboard = InlineKeyboardMarkup(row_width=2)
        keyboard.add(*[InlineKeyboardButton(name, callback_data=f"sender_{name}") for name in [
            "АВ Металл Групп", "Викант", "Вартис", "Парк Плюс"
        ]])
        keyboard.add(InlineKeyboardButton("Написать отправителя", callback_data="custom_sender"))
        await bot.send_message(callback_query.from_user.id, "Выберите отправителя:", reply_markup=keyboard)
    else:
        keyboard = InlineKeyboardMarkup(row_width=2)
        keyboard.add(InlineKeyboardButton("Кривой Рог Цемент", callback_data="sender_Кривой Рог Цемент"))
        keyboard.add(InlineKeyboardButton("Написать отправителя", callback_data="custom_sender"))
        await bot.send_message(callback_query.from_user.id, "Выберите товаро-отправителя:", reply_markup=keyboard)

# Ввод пользовательского отправителя
@dp.callback_query_handler(lambda c: c.data == "custom_sender")
async def custom_sender_handler(callback_query: CallbackQuery):
    await bot.send_message(callback_query.from_user.id, "Введите название отправителя текстом:")

@dp.message_handler()
async def custom_sender_text_handler(message: types.Message):
    user_data[message.from_user.id]['sender'] = message.text
    await ask_unloading_status(message.from_user.id)

# Статус разгрузки
async def ask_unloading_status(user_id):
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton("Разгружено", callback_data="status_unloaded"))
    keyboard.add(InlineKeyboardButton("Не разгружено", callback_data="status_not_unloaded"))
    await bot.send_message(user_id, "Выберите статус разгрузки:", reply_markup=keyboard)

@dp.callback_query_handler(lambda c: c.data.startswith("status"))
async def unloading_status_handler(callback_query: CallbackQuery):
    status = "Разгружено" if callback_query.data == "status_unloaded" else "Не разгружено"
    user_data[callback_query.from_user.id]['status'] = status
    await confirm_order(callback_query.from_user.id)

# Подтверждение заказа
async def confirm_order(user_id):
    data = user_data[user_id]
    transport = "Автомобилем" if data['scenario'] == "scenario_1" else "Вагонами"
    message = (
        f"Подтвердите:\n"
        f"Транспортировка: {transport}\n"
        f"Груз: {data['cargo']}\n"
        f"Отправитель: {data['sender']}\n"
        f"Статус разгрузки: {data['status']}"
    )
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton("Подтвердить", callback_data="confirm"))
    keyboard.add(InlineKeyboardButton("Отмена", callback_data="cancel"))
    await bot.send_message(user_id, message, reply_markup=keyboard)

# Подтверждение и отправка в канал
@dp.callback_query_handler(lambda c: c.data == "confirm")
async def confirm_handler(callback_query: CallbackQuery):
    data = user_data.pop(callback_query.from_user.id, {})
    transport = "Автомобилем" if data['scenario'] == "scenario_1" else "Вагонами"
    message = (
        f"Новый заказ:\n"
        f"Транспортировка: {transport}\n"
        f"Груз: {data['cargo']}\n"
        f"Отправитель: {data['sender']}\n"
        f"Статус разгрузки: {data['status']}"
    )
    await bot.send_message(CHANNEL_ID, message)
    await bot.send_message(callback_query.from_user.id, "Данные отправлены в канал!")

# Отмена заказа
@dp.callback_query_handler(lambda c: c.data == "cancel")
async def cancel_handler(callback_query: CallbackQuery):
    user_data.pop(callback_query.from_user.id, None)
    await bot.send_message(callback_query.from_user.id, "Отменено.")

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
