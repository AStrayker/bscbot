import logging
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.utils import executor
from aiogram.dispatcher import FSMContext

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

# Функция для отправки сообщения с клавиатурой
async def send_message_with_keyboard(user_id, text, keyboard):
    try:
        await bot.send_message(user_id, text, reply_markup=keyboard)
    except Exception as e:
        logger.error(f"Ошибка отправки сообщения: {e}")

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

    await send_message_with_keyboard(user_id, "Выберите груз:", keyboard)

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
        await send_message_with_keyboard(user_id, "Уточните тип металлопроката:", keyboard)
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

    await send_message_with_keyboard(user_id, "Выберите отправителя:", keyboard)

# Шаг 5: Выбор количества машин
@dp.callback_query_handler(lambda c: c.data.startswith('quantity'))
async def quantity_handler(callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    quantity = callback_query.data.split('_')[1]
    user_data[user_id]['quantity'] = quantity

    # Формирование итогового сообщения
    transport = user_data[user_id].get('transport', '')
    cargo = user_data[user_id].get('cargo', '')
    sender = user_data[user_id].get('sender', '')
    message = f"Ваш заказ подтвержден!\n\nТранспорт: {transport}\nГруз: {cargo}\nОтправитель: {sender}\nКоличество машин: {quantity}"

    # Отправка подтверждения в канал
    await bot.send_message(CHANNEL_ID, message)

    # Уведомление для пользователя
    await callback_query.message.edit_text("Ваш заказ успешно подтвержден!")

    # Возврат к шагу 2 с кнопками для выбора способа транспортировки
    await transport_step(callback_query.message)

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
    await transport_step(callback_query.message)

# Шаг 7: Отмена
@dp.callback_query_handler(lambda c: c.data == "cancel")
async def cancel_handler(callback_query: CallbackQuery):
    await callback_query.message.edit_text("Ваш заказ отменен.")

    # Возврат к шагу 2
    await transport_step(callback_query.message)

# Шаг 2: Функция для отправки кнопок выбора транспорта
async def transport_step(message: types.Message):
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton("🚛Автомобилем", callback_data="transport_auto"))
    keyboard.add(InlineKeyboardButton("🚂Вагонами", callback_data="transport_train"))
    await message.answer("Выберите способ транспортировки:", reply_markup=keyboard)

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
