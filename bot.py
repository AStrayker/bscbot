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
        InlineKeyboardButton("Автомобилем", callback_data="transport_auto"),
        InlineKeyboardButton("Вагонами", callback_data="transport_train")
    )
    await bot.send_message(user_id, "Выберите способ транспортировки:", reply_markup=keyboard)

# Шаг 1: Начало сценария
@dp.message_handler(commands=['start'])
async def start_handler(message: types.Message):
    user_data[message.from_user.id] = {}
    await send_start_message(message.from_user.id)

# Шаг 2: Выбор груза
@dp.callback_query_handler(lambda c: c.data.startswith('transport'))
async def transport_handler(callback_query: CallbackQuery):
    transport_type = "Автомобилем" if callback_query.data == "transport_auto" else "Вагонами"
    user_data[callback_query.from_user.id]['transport'] = transport_type

    # Кнопки для выбора груза
    keyboard = InlineKeyboardMarkup(row_width=2)
    cargo_options = [
        "Песок", "Цемент М500", "Цемент М400", "Щебень 5x10",
        "Щебень 5x20", "Щебень 10x20", "Щебень 20x40", "Металлопрокат"
    ]
    for cargo in cargo_options:
        keyboard.add(InlineKeyboardButton(cargo, callback_data=f"cargo_{cargo}"))
    
    await bot.send_message(callback_query.from_user.id, "Выберите груз:", reply_markup=keyboard)

# Шаг 3: Если выбран Металлопрокат, уточняем тип груза
@dp.callback_query_handler(lambda c: c.data.startswith('cargo'))
async def cargo_handler(callback_query: CallbackQuery):
    cargo = callback_query.data.split('_')[1]
    user_data[callback_query.from_user.id]['cargo'] = cargo

    if cargo == "Металлопрокат":
        keyboard = InlineKeyboardMarkup(row_width=2)
        keyboard.add(
            InlineKeyboardButton("Проволока", callback_data="metal_provoloka"),
            InlineKeyboardButton("Металлопрокат", callback_data="metal_metal")
        )
        await bot.send_message(callback_query.from_user.id, "Выберите тип груза:", reply_markup=keyboard)
    else:
        await choose_sender(callback_query.from_user.id)

@dp.callback_query_handler(lambda c: c.data.startswith('metal'))
async def metal_handler(callback_query: CallbackQuery):
    metal_type = "Проволока" if callback_query.data == "metal_provoloka" else "Металлопрокат"
    user_data[callback_query.from_user.id]['cargo'] = metal_type
    await choose_sender(callback_query.from_user.id)

# Шаг 4: Выбор отправителя
async def choose_sender(user_id):
    keyboard = InlineKeyboardMarkup(row_width=2)
    sender_options = [
        "Кривой Рог Цемент", "СпецКарьер", "Смарт Гранит",
        "Баловские Пески", "Любимовский Карьер", "ТОВ МКК №3", "Новатор"
    ]
    for sender in sender_options:
        keyboard.add(InlineKeyboardButton(sender, callback_data=f"sender_{sender}"))
    
    await bot.send_message(user_id, "Выберите отправителя:", reply_markup=keyboard)

@dp.callback_query_handler(lambda c: c.data.startswith('sender'))
async def sender_handler(callback_query: CallbackQuery):
    sender = callback_query.data.split('_')[1]
    user_data[callback_query.from_user.id]['sender'] = sender

    transport = user_data[callback_query.from_user.id].get('transport', '')

    if transport == "Автомобилем":
        # Для автомобилей: Указать количество машин
        keyboard = InlineKeyboardMarkup(row_width=3)
        for i in range(1, 6):
            keyboard.add(InlineKeyboardButton(str(i), callback_data=f"quantity_{i}"))
        await bot.send_message(callback_query.from_user.id, "Укажите количество машин (или введите текстом):", reply_markup=keyboard)
        await OrderState.choosing_quantity.set()
    elif transport == "Вагонами":
        # Для вагонов: Указать статус
        keyboard = InlineKeyboardMarkup(row_width=2)
        keyboard.add(
            InlineKeyboardButton("Разгружено", callback_data="status_unloaded"),
            InlineKeyboardButton("Не разгружено", callback_data="status_not_unloaded"),
            InlineKeyboardButton("Не указано", callback_data="status_not_specified")
        )
        await bot.send_message(callback_query.from_user.id, "Выберите статус:", reply_markup=keyboard)
        await OrderState.choosing_status.set()

# Шаг 5: Указание количества машин
@dp.callback_query_handler(lambda c: c.data.startswith('quantity'), state=OrderState.choosing_quantity)
async def quantity_handler(callback_query: CallbackQuery, state: FSMContext):
    quantity = callback_query.data.split('_')[1]
    user_data[callback_query.from_user.id]['quantity'] = quantity
    await state.finish()
    await confirm_order(callback_query.from_user.id)

@dp.message_handler(state=OrderState.choosing_quantity)
async def quantity_text_handler(message: types.Message, state: FSMContext):
    user_data[message.from_user.id]['quantity'] = message.text
    await state.finish()
    await confirm_order(message.from_user.id)

# Шаг 5: Указание статуса для вагонов
@dp.callback_query_handler(lambda c: c.data.startswith('status'), state=OrderState.choosing_status)
async def status_handler(callback_query: CallbackQuery, state: FSMContext):
    status_map = {
        "status_unloaded": "Разгружено",
        "status_not_unloaded": "Не разгружено",
        "status_not_specified": "Не указано"
    }
    status = status_map[callback_query.data]
    user_data[callback_query.from_user.id]['status'] = status
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

# Отмена
@dp.callback_query_handler(lambda c: c.data == "cancel")
async def cancel_handler(callback_query: CallbackQuery):
    user_data.pop(callback_query.from_user.id, None)
    await bot.send_message(callback_query.from_user.id, "Ваш заказ отменен.")
    await send_start_message(callback_query.from_user.id)

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
