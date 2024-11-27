# bot.py
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

# Временное хранилище данных пользователей
user_data = {}

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

# Функция для возврата к начальному сообщению
async def send_start_message(user_id):
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton("А🚛втомобилем", callback_data="transport_auto"),
        InlineKeyboardButton("🚂Вагонами", callback_data="transport_train")
    )
    await bot.send_message(user_id, "Выберите способ транспортировки:", reply_markup=keyboard)

# Шаг 1: Начало сценария
@dp.message_handler(commands=['start'])
async def start_handler(message: types.Message):
    user_data[message.from_user.id] = {}
    await send_start_message(message.from_user.id)

# Функция для отправки сообщения на "Шаг 2: Выбор способа транспортировки"
async def send_transport_choice(user_id):
    # Убедитесь, что все состояния завершены
    state = dp.current_state(chat=user_id, user=user_id)
    await state.reset_state(with_data=False)  # Полностью очищаем состояние перед следующим шагом

    # Создаем клавиатуру для выбора способа транспортировки
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton("🚛Автомобилем", callback_data="transport_auto"),
        InlineKeyboardButton("🚂Вагонами", callback_data="transport_train")
    )
    await bot.send_message(user_id, "Выберите способ транспортировки:", reply_markup=keyboard)

# Шаг 7: Подтверждение
@dp.callback_query_handler(lambda c: c.data == "confirm")
async def confirm_handler(callback_query: CallbackQuery):
    data = user_data.pop(callback_query.from_user.id, {})
    transport = data.get('transport', 'Не указан')
    cargo = data.get('cargo', 'Не указан')
    sender = data.get('sender', 'Не указан')
    quantity = data.get('quantity', 'Не указано')
    status = data.get('status', 'Не указано')

    message = (
        f"🚛Новое поступление🔔\n"
        f"_______\n"
        f"Транспортировка: {transport}\n"
        f"Груз: {cargo}\n"
        f"Отправитель: {sender}\n"
    )
    if transport == "🚛Автомобилем":
        message += f"Количество машин: {quantity}\n"
    elif transport == "🚂Вагонами":
        message += f"Статус: {status}\n"

    await bot.send_message(CHANNEL_ID, message)
    await callback_query.answer("Данные успешно отправлены!")

    # Возвращаемся к выбору транспортировки
    await send_transport_choice(callback_query.from_user.id)

# Шаг 8: Отмена
@dp.callback_query_handler(lambda c: c.data == "cancel")
async def cancel_handler(callback_query: CallbackQuery):
    user_data.pop(callback_query.from_user.id, None)
    await callback_query.answer("Операция отменена.")
    await send_transport_choice(callback_query.from_user.id)
