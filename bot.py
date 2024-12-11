# файл: telegram_transport_bot.py
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.utils import executor
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.dispatcher import FSMContext
from aiogram.contrib.fsm_storage.memory import MemoryStorage

# Telegram токен
API_TOKEN = '6072615655:AAHQh3BVU3HNHd3p7vfvE3JsBzfHiG-hNMU'
CHANNEL_ID = '@precoinmarket_channel'

# Настройка логгирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Инициализация бота и диспетчера
bot = Bot(token=API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

# FSM (состояния)
class OrderState(StatesGroup):
    choosing_quantity = State()
    choosing_status = State()

# Временное хранилище данных пользователей
user_data = {}

# Общая функция для отправки сообщения с клавиатурой
async def send_message_with_keyboard(user_id, text, keyboard):
    try:
        await bot.send_message(user_id, text, reply_markup=keyboard)
    except Exception as e:
        logger.error(f"Ошибка отправки сообщения: {e}")

# Шаг 1: Начало сценария
@dp.message_handler(commands=['start'])
async def start_handler(message: types.Message):
    user_data[message.from_user.id] = {}
    keyboard = InlineKeyboardMarkup(row_width=2).add(
        InlineKeyboardButton("🚛Автомобилем", callback_data="transport_auto"),
        InlineKeyboardButton("🚂Вагонами", callback_data="transport_train")
    )
    await send_message_with_keyboard(message.from_user.id, "Выберите способ транспортировки:", keyboard)

# Шаг 2: Выбор способа транспортировки
async def step_2_transport(user_id):
    keyboard = InlineKeyboardMarkup(row_width=2).add(
        InlineKeyboardButton("🚛Автомобилем", callback_data="transport_auto"),
        InlineKeyboardButton("🚂Вагонами", callback_data="transport_train")
    )
    await send_message_with_keyboard(user_id, "Выберите способ транспортировки:", keyboard)

@dp.callback_query_handler(lambda c: c.data.startswith('transport'))
async def transport_handler(callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    transport_type = "🚛Автомобилем" if callback_query.data == "transport_auto" else "🚂Вагонами"
    user_data[user_id]['transport'] = transport_type

    cargo_options = [
        "Песок", "Цемент М500", "Цемент М400", "Щебень 5x10",
        "Щебень 5x20", "Щебень 10x20", "Щебень 20x40", "Металлопрокат"
    ]
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(*(InlineKeyboardButton(cargo, callback_data=f"cargo_{cargo}") for cargo in cargo_options))

    await send_message_with_keyboard(user_id, "Выберите груз:", keyboard)

# Обработчики подтверждения и отмены
@dp.callback_query_handler(lambda c: c.data == "confirm")
async def confirm_handler(callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    data = user_data.pop(user_id, {})
    if not data:
        await callback_query.answer("Ошибка: данные не найдены.")
        return

    message = (
        f"🚛Новое поступление🔔\n"
        f"_______\n"
        f"Транспортировка: {data.get('transport', 'Не указано')}\n"
        f"Груз: {data.get('cargo', 'Не указано')}\n"
        f"Отправитель: {data.get('sender', 'Не указано')}\n"
    )
    await bot.send_message(CHANNEL_ID, message)
    await callback_query.answer("Данные успешно отправлены.")
    # Возврат к шагу 2
    await step_2_transport(user_id)

@dp.callback_query_handler(lambda c: c.data == "cancel")
async def cancel_handler(callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    user_data.pop(user_id, None)
    await callback_query.answer("Отправка отменена.")
    # Возврат к шагу 2
    await step_2_transport(user_id)

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
