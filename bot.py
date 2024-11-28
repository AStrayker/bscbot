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

# Шаг 1: Начало сценария
@dp.message_handler(commands=['start'])
async def start_handler(message: types.Message):
    # Очищаем пользовательские данные
    user_data.pop(message.from_user.id, None)
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton("🚛Автомобилем", callback_data="transport_auto"))
    keyboard.add(InlineKeyboardButton("🚂Вагонами", callback_data="transport_train"))
    await message.answer("Выберите способ транспортировки:", reply_markup=keyboard)

# Шаг 2: Выбор способа транспортировки
@dp.callback_query_handler(lambda c: c.data.startswith('transport'))
async def transport_handler(callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    transport_type = "🚛Автомобилем" if callback_query.data == "transport_auto" else "🚂Вагонами"
    user_data[user_id] = {'transport': transport_type}

    cargo_options = [
        "Песок", "Цемент М500", "Цемент М400", "Щебень 5x10",
        "Щебень 5x20", "Щебень 10x20", "Щебень 20x40", "Металлопрокат"
    ]
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(*(InlineKeyboardButton(cargo, callback_data=f"cargo_{cargo}") for cargo in cargo_options))

    await callback_query.message.edit_text("Выберите груз:", reply_markup=keyboard)

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
        await callback_query.message.edit_text("Уточните тип металлопроката:", reply_markup=keyboard)
    else:
        await choose_sender(callback_query)

# Шаг 3.1: Тип металлопроката
@dp.callback_query_handler(lambda c: c.data.startswith('metal'))
async def metal_handler(callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    metal_type = "Проволока" if callback_query.data == "metal_provoloka" else "Металлопрокат"
    user_data[user_id]['cargo'] = metal_type
    await choose_sender(callback_query)

# Шаг 4: Выбор отправителя
async def choose_sender(callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    sender_options = [
        "Кривой Рог Цемент", "СпецКарьер", "Смарт Гранит",
        "Баловские Пески", "Любимовский Карьер", "ТОВ МКК №3", "Новатор"
    ]
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(*(InlineKeyboardButton(sender, callback_data=f"sender_{sender}") for sender in sender_options))

    await callback_query.message.edit_text("Выберите отправителя:", reply_markup=keyboard)

# Шаг 5: Подтверждение данных
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
        await callback_query.message.edit_text("Укажите количество машин (или введите текстом):", reply_markup=keyboard)
    elif transport == "🚂Вагонами":
        keyboard = InlineKeyboardMarkup(row_width=2).add(
            InlineKeyboardButton("🟢Разгружено", callback_data="status_unloaded"),
            InlineKeyboardButton("🟡Не разгружено", callback_data="status_not_unloaded"),
            InlineKeyboardButton("🟠Не указано", callback_data="status_not_specified")
        )
        await callback_query.message.edit_text("Укажите статус:", reply_markup=keyboard)

# Шаг 6: Подтверждение
@dp.callback_query_handler(lambda c: c.data == "confirm")
async def confirm_handler(callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    data = user_data[user_id]

    # Формирование сообщения
    message = f"Ваш заказ подтвержден!\n\nТранспорт: {data.get('transport')}\nГруз: {data.get('cargo')}\nОтправитель: {data.get('sender')}"
    
    # Отправка подтверждения в канал
    await bot.send_message(CHANNEL_ID, message)

    # Уведомление для пользователя
    await callback_query.message.edit_text("Ваш заказ успешно подтвержден!")
    
    # Возврат к шагу 2 с кнопками для выбора способа транспортировки
    await choose_transport(callback_query.message)

# Шаг 7: Отмена
@dp.callback_query_handler(lambda c: c.data == "cancel")
async def cancel_handler(callback_query: CallbackQuery):
    await callback_query.message.edit_text("Ваш заказ отменен.")
    
    # Возврат к шагу 2
    await choose_transport(callback_query.message)

# Шаг 2: Функция для отправки кнопок выбора транспорта
async def choose_transport(message: types.Message):
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton("🚛Автомобилем", callback_data="transport_auto"))
    keyboard.add(InlineKeyboardButton("🚂Вагонами", callback_data="transport_train"))
    await message.answer("Выберите способ транспортировки:", reply_markup=keyboard)

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
