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


# Функция для отправки сообщения из шага 2 (Выбор способа транспортировки)
async def send_transport_choice(user_id):
    keyboard = InlineKeyboardMarkup(row_width=2).add(
        InlineKeyboardButton("🚛Автомобилем", callback_data="transport_auto"),
        InlineKeyboardButton("🚂Вагонами", callback_data="transport_train")
    )
    await bot.send_message(user_id, "Выберите способ транспортировки:", reply_markup=keyboard)


# Шаг 1: Начало сценария
@dp.message_handler(commands=['start'])
async def start_handler(message: types.Message):
    user_data[message.from_user.id] = {}
    await send_transport_choice(message.from_user.id)


# Шаг 2: Выбор способа транспортировки
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

    await bot.send_message(user_id, "Выберите груз:", reply_markup=keyboard)


# Шаг 3: Выбор груза
@dp.callback_query_handler(lambda c: c.data.startswith('cargo'))
async def cargo_handler(callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    cargo = callback_query.data.split('_')[1]
    user_data[user_id]['cargo'] = cargo

    if cargo == "Металлопрокат":
        keyboard = InlineKeyboardMarkup(row_width=2).add(
            InlineKeyboardButton("Проволока", callback_data="metal_provoloka"),
            InlineKeyboardButton("Металлопрокат", callback_data="metal_metal")
        )
        await bot.send_message(user_id, "Уточните тип металлопроката:", reply_markup=keyboard)
    else:
        await choose_sender(user_id)


# Шаг 3.1: Тип металлопроката
@dp.callback_query_handler(lambda c: c.data.startswith('metal'))
async def metal_handler(callback_query: CallbackQuery):
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

    await bot.send_message(user_id, "Выберите отправителя:", reply_markup=keyboard)


@dp.callback_query_handler(lambda c: c.data.startswith('sender'))
async def sender_handler(callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    sender = callback_query.data.split('_')[1]
    user_data[user_id]['sender'] = sender

    transport = user_data[user_id].get('transport', '')

    if transport == "🚛Автомобилем":
        keyboard = InlineKeyboardMarkup(row_width=3).add(
            *(InlineKeyboardButton(str(i), callback_data=f"quantity_{i}") for i in range(1, 6))
        )
        await bot.send_message(user_id, "Укажите количество машин (или введите текстом):", reply_markup=keyboard)
        await OrderState.choosing_quantity.set()
    elif transport == "🚂Вагонами":
        keyboard = InlineKeyboardMarkup(row_width=2).add(
            InlineKeyboardButton("🟢Разгружено", callback_data="status_unloaded"),
            InlineKeyboardButton("🟡Не разгружено", callback_data="status_not_unloaded"),
            InlineKeyboardButton("🟠Не указано", callback_data="status_not_specified")
        )
        await bot.send_message(user_id, "Укажите статус:", reply_markup=keyboard)
        await OrderState.choosing_status.set()


# Шаг 5: Указание количества машин
@dp.callback_query_handler(lambda c: c.data.startswith('quantity'), state=OrderState.choosing_quantity)
async def quantity_handler(callback_query: CallbackQuery, state: FSMContext):
    user_id = callback_query.from_user.id
    quantity = callback_query.data.split('_')[1]
    user_data[user_id]['quantity'] = quantity
    await state.finish()
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
    await state.finish()
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
        InlineKeyboardButton("Подтвердить", callback_data="confirm"),
        InlineKeyboardButton("Отмена", callback_data="cancel")
    )
    await bot.send_message(user_id, message, reply_markup=keyboard)


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
    if data.get('transport') == "🚛Автомобилем":
        message += f"Количество машин: {data.get('quantity', 'Не указано')}\n"
    elif data.get('transport') == "🚂Вагонами":
        message += f"Статус: {data.get('status', 'Не указано')}\n"

    try:
        await bot.send_message(CHANNEL_ID, message)
        await callback_query.message.answer("Данные успешно отправлены в канал!")
    except Exception as e:
        logger.error(f"Ошибка отправки в канал: {e}")
        await callback_query.message.answer("Ошибка при отправке в канал.")

    # Возврат к шагу 2
async def send_transport_choice(user_id):


@dp.callback_query_handler(lambda c: c.data == "cancel")
async def cancel_handler(callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    user_data.pop(user_id, None)
    await callback_query.message.answer("Вы отменили ввод. Начните заново с выбора способа транспортировки.")
    await send_transport_choice(user_id)


if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
