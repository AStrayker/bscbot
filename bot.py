# bot.py
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.utils import executor

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


# Функция возврата к стартовому шагу
async def go_to_start(user_id):
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton("Сообщить о товаре", callback_data="scenario_1"))
    keyboard.add(InlineKeyboardButton("Товар в вагонах", callback_data="scenario_2"))
    await bot.send_message(user_id, "Выберите следующий вариант:", reply_markup=keyboard)


# Шаг 1: Начало сценария
@dp.message_handler(commands=['start'])
async def start_handler(message: types.Message):
    user_data[message.from_user.id] = {}
    await go_to_start(message.from_user.id)


# Шаг 2: Обработка сценария
@dp.callback_query_handler(lambda c: c.data.startswith('scenario'))
async def scenario_handler(callback_query: CallbackQuery):
    scenario = callback_query.data
    user_data[callback_query.from_user.id] = {'scenario': scenario}
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(*[InlineKeyboardButton(name, callback_data=f"cargo_{name}") for name in [
        "Песок", "Цемент М500", "Цемент М400", "Щебень 5x10", "Щебень 5x20", "Щебень 10x20", "Щебень 20x40", "Металлопрокат"
    ]])
    await callback_query.message.edit_text("Выберите тип или марку/фракцию груза:", reply_markup=keyboard)


# Шаг 3: Выбор отправителя
@dp.callback_query_handler(lambda c: c.data.startswith('cargo'))
async def cargo_handler(callback_query: CallbackQuery):
    cargo = callback_query.data.split('_')[1]
    user_data[callback_query.from_user.id]['cargo'] = cargo

    # Специальный сценарий для "Металлопрокат"
    if cargo == "Металлопрокат":
        keyboard = InlineKeyboardMarkup(row_width=2)
        keyboard.add(
            InlineKeyboardButton("Проволока", callback_data="metal_wire"),
            InlineKeyboardButton("Металлопрокат", callback_data="metal_roll"),
            InlineKeyboardButton("Отмена", callback_data="cancel")
        )
        await callback_query.message.edit_text("Выберите груз:", reply_markup=keyboard)
        return

    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(*[InlineKeyboardButton(name, callback_data=f"sender_{name}") for name in [
        "Кривой рог цемент", "СпецКарьер", "Смарт Гранит", "Баловские пески", "Любимовский карьер", "Бородавский карьер", "ТОВ МКК №3", "Новатор"
    ]])
    await callback_query.message.edit_text("Выберите товаро-отправителя:", reply_markup=keyboard)


# Шаг 4: Выбор количества машин
@dp.callback_query_handler(lambda c: c.data.startswith('sender'))
async def sender_handler(callback_query: CallbackQuery):
    sender = callback_query.data.split('_')[1]
    user_data[callback_query.from_user.id]['sender'] = sender

    keyboard = InlineKeyboardMarkup(row_width=3)
    keyboard.add(
        InlineKeyboardButton("1", callback_data="quantity_1"),
        InlineKeyboardButton("2", callback_data="quantity_2"),
        InlineKeyboardButton("3", callback_data="quantity_3"),
        InlineKeyboardButton("4", callback_data="quantity_4"),
        InlineKeyboardButton("5", callback_data="quantity_5"),
        InlineKeyboardButton("Свое значение", callback_data="custom_quantity")
    )
    await callback_query.message.edit_text("Выберите количество машин:", reply_markup=keyboard)


# Шаг 5: Подтверждение
@dp.callback_query_handler(lambda c: c.data.startswith('quantity'))
async def quantity_handler(callback_query: CallbackQuery):
    quantity = callback_query.data.split('_')[1]
    user_data[callback_query.from_user.id]['quantity'] = quantity

    # Формируем текст подтверждения
    data = user_data[callback_query.from_user.id]
    transport = "Автомобилем" if data['scenario'] == "scenario_1" else "Вагонами"
    message = (
        f"Подтвердите:\n"
        f"Транспортировка: {transport}\n"
        f"Груз: {data['cargo']}\n"
        f"Отправитель: {data['sender']}\n"
        f"Количество: {quantity}"
    )

    keyboard = InlineKeyboardMarkup()
    keyboard.add(
        InlineKeyboardButton("Редактировать", callback_data="edit"),
        InlineKeyboardButton("Подтвердить", callback_data="confirm"),
        InlineKeyboardButton("Отмена", callback_data="cancel")
    )
    await callback_query.message.edit_text(message, reply_markup=keyboard)


# Шаг 6: Редактирование
@dp.callback_query_handler(lambda c: c.data == "edit")
async def edit_handler(callback_query: CallbackQuery):
    keyboard = InlineKeyboardMarkup()
    keyboard.add(
        InlineKeyboardButton("Изменить груз", callback_data="edit_cargo"),
        InlineKeyboardButton("Изменить отправителя", callback_data="edit_sender"),
        InlineKeyboardButton("Изменить количество", callback_data="edit_quantity"),
        InlineKeyboardButton("Не редактировать", callback_data="no_edit")
    )
    await callback_query.message.edit_text("Выберите, что хотите изменить:", reply_markup=keyboard)


# Шаг 7: Подтверждение и отправка
@dp.callback_query_handler(lambda c: c.data == "confirm")
async def confirm_handler(callback_query: CallbackQuery):
    data = user_data.pop(callback_query.from_user.id, {})
    transport = "Автомобилем" if data['scenario'] == "scenario_1" else "Вагонами"
    message = (
        f"Новый заказ:\n"
        f"Транспортировка: {transport}\n"
        f"Груз: {data['cargo']}\n"
        f"Отправитель: {data['sender']}\n"
        f"Количество: {data['quantity']}"
    )

    # Логика для "Металлопрокат"
    if data['cargo'] == "Металлопрокат":
        await bot.send_message(callback_query.from_user.id, message)
    else:
        await bot.send_message(CHANNEL_ID, message)

    await go_to_start(callback_query.from_user.id)


# Шаг 8: Обработка отмены
@dp.callback_query_handler(lambda c: c.data == "cancel")
async def cancel_handler(callback_query: CallbackQuery):
    user_data.pop(callback_query.from_user.id, None)
    await callback_query.message.edit_text("Отменено.")
    await go_to_start(callback_query.from_user.id)


if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
