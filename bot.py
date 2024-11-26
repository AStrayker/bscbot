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

# Вспомогательная функция: Создание кнопок
def create_keyboard(buttons, row_width=2):
    keyboard = InlineKeyboardMarkup(row_width=row_width)
    for button in buttons:
        keyboard.add(InlineKeyboardButton(button, callback_data=button))
    return keyboard

# Возврат к начальному сообщению
async def send_start_message(user_id):
    transport_keyboard = create_keyboard(["Автомобилем", "Вагонами"], row_width=2)
    await bot.send_message(user_id, "Выберите способ транспортировки:", reply_markup=transport_keyboard)

# Шаг 1: Начало сценария
@dp.message_handler(commands=['start'])
async def start_handler(message: types.Message):
    user_data[message.from_user.id] = {}
    await send_start_message(message.from_user.id)

# Шаг 2: Выбор груза
@dp.callback_query_handler(lambda c: c.data in ["Автомобилем", "Вагонами"])
async def transport_handler(callback_query: CallbackQuery):
    transport_type = callback_query.data
    user_data[callback_query.from_user.id]['transport'] = transport_type

    # Кнопки для выбора груза
    cargo_options = [
        "Песок", "Цемент М500", "Цемент М400", "Щебень 5x10",
        "Щебень 5x20", "Щебень 10x20", "Щебень 20x40", "Металлопрокат"
    ]
    cargo_keyboard = create_keyboard(cargo_options)
    await bot.send_message(callback_query.from_user.id, "Выберите груз:", reply_markup=cargo_keyboard)

# Шаг 3: Если выбран Металлопрокат, уточняем тип груза
@dp.callback_query_handler(lambda c: c.data in [
    "Песок", "Цемент М500", "Цемент М400", "Щебень 5x10",
    "Щебень 5x20", "Щебень 10x20", "Щебень 20x40", "Металлопрокат"
])
async def cargo_handler(callback_query: CallbackQuery):
    cargo = callback_query.data
    user_data[callback_query.from_user.id]['cargo'] = cargo

    if cargo == "Металлопрокат":
        metal_options = ["Проволока", "Металлопрокат"]
        metal_keyboard = create_keyboard(metal_options)
        await bot.send_message(callback_query.from_user.id, "Выберите тип груза:", reply_markup=metal_keyboard)
    else:
        await choose_sender(callback_query.from_user.id)

@dp.callback_query_handler(lambda c: c.data in ["Проволока", "Металлопрокат"])
async def metal_handler(callback_query: CallbackQuery):
    user_data[callback_query.from_user.id]['cargo'] = callback_query.data
    await choose_sender(callback_query.from_user.id)

# Шаг 4: Выбор отправителя
async def choose_sender(user_id):
    sender_options = [
        "Кривой Рог Цемент", "СпецКарьер", "Смарт Гранит",
        "Баловские Пески", "Любимовский Карьер", "ТОВ МКК №3", "Новатор"
    ]
    sender_keyboard = create_keyboard(sender_options)
    await bot.send_message(user_id, "Выберите отправителя:", reply_markup=sender_keyboard)

@dp.callback_query_handler(lambda c: c.data in [
    "Кривой Рог Цемент", "СпецКарьер", "Смарт Гранит",
    "Баловские Пески", "Любимовский Карьер", "ТОВ МКК №3", "Новатор"
])
async def sender_handler(callback_query: CallbackQuery):
    user_data[callback_query.from_user.id]['sender'] = callback_query.data
    transport = user_data[callback_query.from_user.id].get('transport', '')

    if transport == "Автомобилем":
        # Для автомобилей: Указать количество машин
        quantity_options = ["1", "2", "3", "4", "5"]
        quantity_keyboard = create_keyboard(quantity_options)
        await bot.send_message(callback_query.from_user.id, "Укажите количество машин:", reply_markup=quantity_keyboard)
        await OrderState.choosing_quantity.set()
    elif transport == "Вагонами":
        # Для вагонов: Указать статус
        status_options = ["Разгружено", "Не разгружено", "Не указано"]
        status_keyboard = create_keyboard(status_options)
        await bot.send_message(callback_query.from_user.id, "Выберите статус:", reply_markup=status_keyboard)
        await OrderState.choosing_status.set()

# Шаг 5: Указание количества машин
@dp.callback_query_handler(lambda c: c.data.isdigit(), state=OrderState.choosing_quantity)
async def quantity_handler(callback_query: CallbackQuery, state: FSMContext):
    user_data[callback_query.from_user.id]['quantity'] = callback_query.data
    await state.finish()
    await confirm_order(callback_query.from_user.id)

# Шаг 5: Указание статуса для вагонов
@dp.callback_query_handler(lambda c: c.data in ["Разгружено", "Не разгружено", "Не указано"], state=OrderState.choosing_status)
async def status_handler(callback_query: CallbackQuery, state: FSMContext):
    user_data[callback_query.from_user.id]['status'] = callback_query.data
    await state.finish()
    await confirm_order(callback_query.from_user.id)

# Шаг 6: Подтверждение заказа
async def confirm_order(user_id):
    data = user_data[user_id]
    transport = data.get('transport', 'Не указан')
    cargo = data.get('cargo', 'Не указан')
    sender = data.get('sender', 'Не указан')
    quantity = data.get('quantity', 'Не указано')
    status = data.get('status', 'Не указано')

    message = (
        f"Подтвердите данные:\n"
        f"Транспортировка: {transport}\n"
        f"Груз: {cargo}\n"
        f"Отправитель: {sender}\n"
    )
    if transport == "Автомобилем":
        message += f"Количество машин: {quantity}\n"
    elif transport == "Вагонами":
        message += f"Статус: {status}\n"
    
    keyboard = InlineKeyboardMarkup()
    keyboard.add(
        InlineKeyboardButton("Подтвердить", callback_data="confirm"),
        InlineKeyboardButton("Отмена", callback_data="cancel")
    )
    await bot.send_message(user_id, message, reply_markup=keyboard)

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
        f"Новый заказ:\n"
        f"Транспортировка: {transport}\n"
        f"Груз: {cargo}\n"
        f"Отправитель: {sender}\n"
    )
    if transport == "Автомобилем":
        message += f"Количество машин: {quantity}\n"
    elif transport == "Вагонами":
        message += f"Статус: {status}\n"

    await bot.send_message(CHANNEL_ID, message)
    await bot.send_message(callback_query.from_user.id, "Ваш заказ подтвержден!")
    await send_start_message(callback_query.from_user.id)

# Отмена
@dp.callback_query_handler(lambda c: c.data == "cancel")
async def cancel_handler(callback_query: CallbackQuery):
    user_data.pop(callback_query.from_user.id, None)
    await bot.send_message(callback_query.from_user.id, "Ваш заказ отменен.")
    await send_start_message(callback_query.from_user.id)

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
