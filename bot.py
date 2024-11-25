# bot.py
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.utils import executor

# Telegram токен
API_TOKEN = '6072615655:AAHQh3BVU3HNHd3p7vfvE3JsBzfHiG-hNMU'
CHANNEL_ID = '@precoinmarket_channel
METAL_RECIPIENTS = [123456789, 987654321]  # ID пользователей для отправки в ЛС

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
    
    if scenario == "scenario_1":
        # Сообщить о товаре
        keyboard = InlineKeyboardMarkup(row_width=2)
        keyboard.add(*[InlineKeyboardButton(name, callback_data=f"cargo_{name}") for name in [
            "Металлопрокат", "Проволока", "Цемент М500", "Щебень 20х40"
        ]])
        await callback_query.message.edit_text("Выберите тип или марку груза:", reply_markup=keyboard)
    elif scenario == "scenario_2":
        # Товар в вагонах
        keyboard = InlineKeyboardMarkup(row_width=2)
        keyboard.add(*[InlineKeyboardButton(name, callback_data=f"cargo_train_{name}") for name in [
            "Цемент М400", "Цемент М500", "Щебень 5х10", "Щебень 5х20", "Щебень 10х20", "Щебень 20х40"
        ]])
        await callback_query.message.edit_text("Выберите груз из вагонов:", reply_markup=keyboard)


# Шаг 3.1: Обработка Металлопрокат или Проволока
@dp.callback_query_handler(lambda c: c.data.startswith("cargo_"))
async def cargo_handler(callback_query: CallbackQuery):
    cargo = callback_query.data.split("_")[1]
    user_data[callback_query.from_user.id]['cargo'] = cargo

    if cargo in ["Металлопрокат", "Проволока"]:
        keyboard = InlineKeyboardMarkup(row_width=2)
        keyboard.add(
            InlineKeyboardButton("АВ Металл Групп", callback_data="metal_sender_АВ_металл_Групп"),
            InlineKeyboardButton("Викант", callback_data="metal_sender_Викант"),
            InlineKeyboardButton("Вартис", callback_data="metal_sender_Вартис"),
            InlineKeyboardButton("Парк Плюс", callback_data="metal_sender_Парк_Плюс"),
            InlineKeyboardButton("Указать вручную", callback_data="manual_sender"),
        )
        await callback_query.message.edit_text(f"Вы выбрали: {cargo}. Укажите отправителя:", reply_markup=keyboard)
    else:
        await callback_query.message.edit_text(f"Вы выбрали: {cargo}. Подтвердите или измените груз.", reply_markup=InlineKeyboardMarkup().add(
            InlineKeyboardButton("Изменить груз", callback_data="change_cargo"),
            InlineKeyboardButton("Подтвердить", callback_data="confirm_cargo")
        ))


# Шаг 3.2: Обработка отправителя
@dp.callback_query_handler(lambda c: c.data.startswith("metal_sender_") or c.data == "manual_sender")
async def sender_handler(callback_query: CallbackQuery):
    if callback_query.data == "manual_sender":
        await callback_query.message.edit_text("Напишите имя отправителя текстом.")
        user_data[callback_query.from_user.id]['awaiting_sender'] = True
    else:
        sender = callback_query.data.split("metal_sender_")[1]
        user_data[callback_query.from_user.id]['sender'] = sender
        await confirm_order(callback_query.message, callback_query.from_user.id)


@dp.message_handler(lambda message: user_data.get(message.from_user.id, {}).get('awaiting_sender'))
async def manual_sender_input(message: types.Message):
    user_data[message.from_user.id]['sender'] = message.text
    user_data[message.from_user.id]['awaiting_sender'] = False
    await confirm_order(message, message.from_user.id)


async def confirm_order(message, user_id):
    data = user_data.get(user_id, {})
    cargo = data.get('cargo', 'не указан')
    sender = data.get('sender', 'не указан')

    text = f"Подтвердите заказ:\nГруз: {cargo}\nОтправитель: {sender}"
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton("Подтвердить", callback_data="confirm_order"))
    keyboard.add(InlineKeyboardButton("Изменить груз", callback_data="change_cargo"))
    keyboard.add(InlineKeyboardButton("Изменить отправителя", callback_data="change_sender"))
    await bot.send_message(user_id, text, reply_markup=keyboard)


# Шаг 4: Подтверждение или изменение данных
@dp.callback_query_handler(lambda c: c.data in ["confirm_order", "change_cargo", "change_sender"])
async def change_or_confirm(callback_query: CallbackQuery):
    action = callback_query.data
    if action == "confirm_order":
        data = user_data.pop(callback_query.from_user.id, {})
        if data.get('cargo') in ["Металлопрокат", "Проволока"]:
            for recipient_id in METAL_RECIPIENTS:
                await bot.send_message(recipient_id, f"Новый заказ:\nГруз: {data['cargo']}\nОтправитель: {data['sender']}")
            await callback_query.message.edit_text("Сообщение отправлено в ЛС.")
        else:
            await bot.send_message(CHANNEL_ID, f"Новый заказ:\nГруз: {data['cargo']}\nОтправитель: {data['sender']}")
            await callback_query.message.edit_text("Сообщение отправлено в канал.")
    elif action == "change_cargo":
        await scenario_handler(callback_query)
    elif action == "change_sender":
        await sender_handler(callback_query)


# Шаг 5: Обработка статуса разгрузки
@dp.callback_query_handler(lambda c: c.data.startswith("cargo_train_"))
async def train_cargo_handler(callback_query: CallbackQuery):
    cargo = callback_query.data.split("cargo_train_")[1]
    user_data[callback_query.from_user.id]['cargo'] = cargo

    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton("Разгружено", callback_data="status_unloaded"),
        InlineKeyboardButton("Не разгружено", callback_data="status_not_unloaded"),
    )
    await callback_query.message.edit_text(f"Вы выбрали груз: {cargo}. Укажите статус разгрузки:", reply_markup=keyboard)


if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
