import logging
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton, CallbackQuery
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

# Глобальные меню
transport_menu = ReplyKeyboardMarkup(resize_keyboard=True).add(
    KeyboardButton("🚛Автомобилем"),
    KeyboardButton("🚂Вагонами"),
)

cargo_menu = ReplyKeyboardMarkup(resize_keyboard=True).add(
    KeyboardButton("Песок"),
    KeyboardButton("Цемент М500"),
    KeyboardButton("Цемент М400"),
    KeyboardButton("Щебень 5x10"),
    KeyboardButton("Щебень 10x20"),
    KeyboardButton("Металлопрокат"),
)

sender_menu = ReplyKeyboardMarkup(resize_keyboard=True).add(
    KeyboardButton("Кривой Рог Цемент"),
    KeyboardButton("СпецКарьер"),
    KeyboardButton("Смарт Гранит"),
    KeyboardButton("Баловские Пески"),
    KeyboardButton("Любимовский Карьер"),
    KeyboardButton("ТОВ МКК №3"),
    KeyboardButton("Новатор"),
)

status_menu = ReplyKeyboardMarkup(resize_keyboard=True).add(
    KeyboardButton("🟢Разгружено"),
    KeyboardButton("🟡Не разгружено"),
    KeyboardButton("🟠Не указано"),
)

confirm_menu = ReplyKeyboardMarkup(resize_keyboard=True).add(
    KeyboardButton("Подтвердить"),
    KeyboardButton("Отменить"),
)


@dp.message_handler(commands=['start'])
async def start_handler(message: types.Message):
    """Начало работы бота."""
    user_data[message.from_user.id] = {}
    await message.answer("Выберите способ транспортировки:", reply_markup=transport_menu)


@dp.message_handler(lambda message: message.text in ["🚛Автомобилем", "🚂Вагонами"])
async def transport_handler(message: types.Message):
    """Выбор способа транспортировки."""
    user_data[message.from_user.id]["transport"] = message.text
    await message.answer("Выберите груз:", reply_markup=cargo_menu)


@dp.message_handler(lambda message: message.text in ["Песок", "Цемент М500", "Цемент М400", "Щебень 5x10", "Щебень 10x20", "Металлопрокат"])
async def cargo_handler(message: types.Message):
    """Выбор груза."""
    user_data[message.from_user.id]["cargo"] = message.text
    if message.text == "Металлопрокат":
        await message.answer("Выберите тип металлопроката:", reply_markup=ReplyKeyboardMarkup(resize_keyboard=True).add(
            KeyboardButton("Проволока"),
            KeyboardButton("Металлопрокат"),
        ))
    else:
        await message.answer("Выберите отправителя:", reply_markup=sender_menu)


@dp.message_handler(lambda message: message.text in ["Проволока", "Металлопрокат"])
async def metal_type_handler(message: types.Message):
    """Уточнение типа металлопроката."""
    user_data[message.from_user.id]["cargo"] = message.text
    await message.answer("Выберите отправителя:", reply_markup=sender_menu)


@dp.message_handler(lambda message: message.text in ["Кривой Рог Цемент", "СпецКарьер", "Смарт Гранит", "Баловские Пески", "Любимовский Карьер", "ТОВ МКК №3", "Новатор"])
async def sender_handler(message: types.Message):
    """Выбор отправителя."""
    user_data[message.from_user.id]["sender"] = message.text
    transport = user_data[message.from_user.id]["transport"]
    if transport == "🚛Автомобилем":
        await message.answer("Укажите количество машин (например: 4):")
        await OrderState.choosing_quantity.set()
    elif transport == "🚂Вагонами":
        await message.answer("Укажите статус:", reply_markup=status_menu)
        await OrderState.choosing_status.set()


@dp.message_handler(state=OrderState.choosing_quantity)
async def quantity_handler(message: types.Message, state: FSMContext):
    """Указание количества машин."""
    if not message.text.isdigit():
        await message.answer("Введите корректное количество машин (число):")
        return

    user_data[message.from_user.id]["quantity"] = message.text
    await state.finish()
    await confirm_order(message.from_user.id)


@dp.message_handler(lambda message: message.text in ["🟢Разгружено", "🟡Не разгружено", "🟠Не указано"], state=OrderState.choosing_status)
async def status_handler(message: types.Message, state: FSMContext):
    """Указание статуса для вагонов."""
    user_data[message.from_user.id]["status"] = message.text
    await state.finish()
    await confirm_order(message.from_user.id)


async def confirm_order(user_id):
    """Подтверждение данных заказа."""
    data = user_data.get(user_id, {})
    if not data:
        await bot.send_message(user_id, "Ошибка: данные не найдены.")
        return

    message = (
        f"Транспортировка: {data.get('transport', 'Не указано')}\n"
        f"Груз: {data.get('cargo', 'Не указано')}\n"
        f"Отправитель: {data.get('sender', 'Не указано')}\n"
    )
    if data.get("transport") == "🚛Автомобилем":
        message += f"Количество машин: {data.get('quantity', 'Не указано')}\n"
    elif data.get("transport") == "🚂Вагонами":
        message += f"Статус: {data.get('status', 'Не указано')}\n"

    await bot.send_message(user_id, message, reply_markup=confirm_menu)


@dp.message_handler(lambda message: message.text == "Подтвердить")
async def confirm_handler(message: types.Message):
    """Подтверждение отправки в канал."""
    user_id = message.from_user.id
    data = user_data.pop(user_id, {})
    if not data:
        await message.answer("Ошибка: данные не найдены.")
        return

    channel_message = (
        f"🚛Новое поступление🔔\n"
        f"_______\n"
        f"Транспортировка: {data.get('transport', 'Не указано')}\n"
        f"Груз: {data.get('cargo', 'Не указано')}\n"
        f"Отправитель: {data.get('sender', 'Не указано')}\n"
    )
    if data.get("transport") == "🚛Автомобилем":
        channel_message += f"Количество машин: {data.get('quantity', 'Не указано')}\n"
    elif data.get("transport") == "🚂Вагонами":
        channel_message += f"Статус: {data.get('status', 'Не указано')}\n"

    await bot.send_message(CHANNEL_ID, channel_message)
    await message.answer("Данные успешно отправлены в канал!", reply_markup=transport_menu)


@dp.message_handler(lambda message: message.text == "Отменить")
async def cancel_handler(message: types.Message):
    """Отмена операции."""
    user_data.pop(message.from_user.id, None)
    await message.answer("Операция отменена.", reply_markup=transport_menu)


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
