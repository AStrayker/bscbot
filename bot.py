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
    choosing_transport = State()
    choosing_cargo = State()
    choosing_sender = State()
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
    user_data[message.from_user.id] = {}  # Очищаем данные перед началом нового сценария
    await choose_transport(message)

# Шаг 2: Выбор способа транспортировки
async def choose_transport(message):
    keyboard = InlineKeyboardMarkup(row_width=2).add(
        InlineKeyboardButton("🚛Автомобилем", callback_data="transport_auto"),
        InlineKeyboardButton("🚂Вагонами", callback_data="transport_train")
    )
    await send_message_with_keyboard(message.from_user.id, "Выберите способ транспортировки:", keyboard)
    await OrderState.choosing_transport.set()

@dp.callback_query_handler(lambda c: c.data.startswith('transport'), state=OrderState.choosing_transport)
async def transport_handler(callback_query: CallbackQuery, state: FSMContext):
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
    await OrderState.choosing_cargo.set()

# Шаг 3: Выбор груза
@dp.callback_query_handler(lambda c: c.data.startswith('cargo'), state=OrderState.choosing_cargo)
async def cargo_handler(callback_query: CallbackQuery, state: FSMContext):
    user_id = callback_query.from_user.id
    cargo = callback_query.data.split('_')[1]
    user_data[user_id]['cargo'] = cargo

    if cargo == "Металлопрокат":
        keyboard = InlineKeyboardMarkup(row_width=2).add(
            InlineKeyboardButton("Проволока", callback_data="metal_provoloka"),
            InlineKeyboardButton("Металлопрокат", callback_data="metal_metal")
        )
        await send_message_with_keyboard(user_id, "Уточните тип металлопроката:", keyboard)
        await OrderState.choosing_sender.set()  # Переводим в состояние выбора отправителя
    else:
        await choose_sender(user_id)

# Шаг 3.1: Тип металлопроката
@dp.callback_query_handler(lambda c: c.data.startswith('metal'), state=OrderState.choosing_sender)
async def metal_handler(callback_query: CallbackQuery, state: FSMContext):
    user_id = callback_query.from_user.id
    metal_type = "Проволока" if callback_query.data == "metal_provoloka" else "Металлопрокат"
    user_data[user_id]['cargo'] = metal_type
    await choose_sender(user_id)

# Шаг 4: Выбор отправителя
async def choose_sender(user_id):
    sender_options = [
        "Кривой Рог Цемент", "СпецКарьер", "Смарт Гранит",
        "Баловские Пески", "Любимовский Карьер", "ТОВ МКК №3", "Новатор"
    ]
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(*(InlineKeyboardButton(sender, callback_data=f"sender_{sender}") for sender in sender_options))

    await send_message_with_keyboard(user_id, "Выберите отправителя:", keyboard)
    await OrderState.choosing_sender.set()

@dp.callback_query_handler(lambda c: c.data.startswith('sender'), state=OrderState.choosing_sender)
async def sender_handler(callback_query: CallbackQuery, state: FSMContext):
    user_id = callback_query.from_user.id
    sender = callback_query.data.split('_')[1]
    user_data[user_id]['sender'] = sender

    transport = user_data[user_id].get('transport', '')

    if transport == "🚛Автомобилем":
        keyboard = InlineKeyboardMarkup(row_width=3).add(
            *(InlineKeyboardButton(str(i), callback_data=f"quantity_{i}") for i in range(1, 6))
        )
        await send_message_with_keyboard(user_id, "Укажите количество машин:", keyboard)
        await OrderState.choosing_quantity.set()
    elif transport == "🚂Вагонами":
        keyboard = InlineKeyboardMarkup(row_width=2).add(
            InlineKeyboardButton("🟢Разгружено", callback_data="status_unloaded"),
            InlineKeyboardButton("🟡Не разгружено", callback_data="status_not_unloaded"),
            InlineKeyboardButton("🟠Не указано", callback_data="status_not_specified")
        )
        await send_message_with_keyboard(user_id, "Укажите статус:", keyboard)
        await OrderState.choosing_status.set()

# Шаг 5: Указание количества машин
@dp.callback_query_handler(lambda c: c.data.startswith('quantity'), state=OrderState.choosing_quantity)
async def quantity_handler(callback_query: CallbackQuery, state: FSMContext):
    user_id = callback_query.from_user.id
    quantity = callback_query.data.split('_')[1]
    user_data[user_id]['quantity'] = quantity
    await state.finish()  # Завершаем состояние
    await confirm_order(user_id)

# Шаг 5: Указание статуса для вагонов
@dp.callback_query_handler(lambda c: c.data.startswith('status'), state=OrderState.choosing_status)
async def status_handler(callback_query: CallbackQuery, state: FSMContext):
    user_id = callback_query.from_user.id
    status_map = {
        "status_unloaded": "🟢Разгружено",
        "status_not_unloaded": "🟡Не разгружено",
        "status_not_specified": "🟠Не указано"
    }
    status = status_map[callback_query.data]
    user_data[user_id]['status'] = status
    await state.finish()  # Завершаем состояние
    await confirm_order(user_id)

# Шаг 6: Подтверждение данных
async def confirm_order(user_id):
    data = user_data.get(user_id, {})
    if not data:
        await bot.send_message(user_id, "Ошибка: данные не найдены.")
        return

    message = (
        f"Подтвердите данные:\n"
        f"Транспортировка: {data.get('transport', 'Не указано')}\n"
        f"Груз: {data.get('cargo', 'Не указано')}\n"
        f"Отправитель: {data.get('sender', 'Не указано')}\n"
    )
    if data.get('transport') == "🚛Автомобилем":
        message += f"Количество машин: {data.get('quantity', 'Не указано')}\n"
    elif data.get('transport') == "🚂Вагонами":
        message += f"Статус: {data.get('status', 'Не указано')}\n"

    keyboard = InlineKeyboardMarkup(row_width=2).add(
        InlineKeyboardButton("✅ Подтвердить", callback_data="confirm"),
        InlineKeyboardButton("❌ Отменить", callback_data="cancel")
    )

    await send_message_with_keyboard(user_id, message, keyboard)

# Подтверждение или отмена
@dp.callback_query_handler(lambda c: c.data == "confirm", state="*")
async def confirm_handler(callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    await bot.send_message(user_id, "Ваш заказ успешно подтвержден!")
    await choose_transport(callback_query.message)

@dp.callback_query_handler(lambda c: c.data == "cancel", state="*")
async def cancel_handler(callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    await bot.send_message(user_id, "Ваш заказ отменен.")
    await choose_transport(callback_query.message)

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
