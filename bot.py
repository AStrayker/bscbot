import logging
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.utils import executor
from aiogram.utils.exceptions import BotBlocked, MessageNotModified

API_TOKEN = '6072615655:AAHQh3BVU3HNHd3p7vfvE3JsBzfHiG-hNMU'  # Замените на токен вашего бота
logging.basicConfig(level=logging.INFO)

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

# Временное хранилище данных пользователей
user_data = {}

# Обработка ошибок
@dp.errors_handler()
async def handle_errors(update, exception):
    if isinstance(exception, BotBlocked):
        logging.warning(f"Bot was blocked by user: {update}")
    elif isinstance(exception, MessageNotModified):
        logging.info("Tried to edit a message with no changes.")
    else:
        logging.error(f"Update: {update} \n{exception}")
    return True

# Стартовая команда
@dp.message_handler(commands=['start'])
async def start_command(message: types.Message):
    user_data[message.from_user.id] = {}
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton("Автомобилями", callback_data="transport_auto"),
        InlineKeyboardButton("Вагонами", callback_data="transport_train")
    )
    await message.answer("Выберите способ транспортировки:", reply_markup=keyboard)

# Выбор транспортировки
@dp.callback_query_handler(lambda c: c.data.startswith('transport_'))
async def transport_selected(callback_query: CallbackQuery):
    transport = callback_query.data.split('_')[1]
    user_data[callback_query.from_user.id]['transport'] = "Автомобилями" if transport == 'auto' else "Вагонами"

    cargo_kb = InlineKeyboardMarkup(row_width=2)
    cargo_kb.add(
        InlineKeyboardButton("Песок", callback_data="cargo_Песок"),
        InlineKeyboardButton("Цемент М400", callback_data="cargo_Цемент_М400"),
        InlineKeyboardButton("Цемент М500", callback_data="cargo_Цемент_М500"),
        InlineKeyboardButton("Щебень 5х10", callback_data="cargo_Щебень_5x10"),
        InlineKeyboardButton("Щебень 5х20", callback_data="cargo_Щебень_5x20"),
        InlineKeyboardButton("Щебень 10х20", callback_data="cargo_Щебень_10x20"),
        InlineKeyboardButton("Щебень 20х40", callback_data="cargo_Щебень_20х40"),
        InlineKeyboardButton("Металлопрокат", callback_data="cargo_Металлопрокат")
    )
    await callback_query.message.edit_text("Выберите груз:", reply_markup=cargo_kb)

# Выбор груза
@dp.callback_query_handler(lambda c: c.data.startswith('cargo_'))
async def cargo_selected(callback_query: CallbackQuery):
    cargo = callback_query.data.split('_')[1]
    user_data[callback_query.from_user.id]['cargo'] = cargo

    if cargo == "Металлопрокат":
        type_kb = InlineKeyboardMarkup(row_width=2)
        type_kb.add(
            InlineKeyboardButton("Проволока", callback_data="type_Проволока"),
            InlineKeyboardButton("Металлопрокат", callback_data="type_Металлопрокат")
        )
        await callback_query.message.edit_text("Выберите тип груза:", reply_markup=type_kb)
    else:
        await show_sender_menu(callback_query)

# Выбор типа груза для металлопроката
@dp.callback_query_handler(lambda c: c.data.startswith('type_'))
async def type_selected(callback_query: CallbackQuery):
    cargo_type = callback_query.data.split('_')[1]
    user_data[callback_query.from_user.id]['cargo'] = cargo_type
    await show_sender_menu(callback_query)

# Меню выбора отправителя
async def show_sender_menu(callback_query: CallbackQuery):
    sender_kb = InlineKeyboardMarkup(row_width=2)
    sender_kb.add(
        InlineKeyboardButton("Кривой Рог Цемент", callback_data="sender_Кривой_Рог_Цемент"),
        InlineKeyboardButton("СпецКарьер", callback_data="sender_СпецКарьер"),
        InlineKeyboardButton("Смарт Гранит", callback_data="sender_Смарт_Гранит"),
        InlineKeyboardButton("Баловские Пески", callback_data="sender_Баловские_Пески"),
        InlineKeyboardButton("Любимовский Карьер", callback_data="sender_Любимовский_Карьер"),
        InlineKeyboardButton("Написать свой вариант", callback_data="sender_custom")
    )
    await callback_query.message.edit_text("Выберите отправителя:", reply_markup=sender_kb)

# Выбор отправителя
@dp.callback_query_handler(lambda c: c.data.startswith('sender_'))
async def sender_selected(callback_query: CallbackQuery):
    sender = callback_query.data.split('_')[1]
    if sender == "custom":
        await callback_query.message.edit_text("Введите имя отправителя текстом:")
        user_data[callback_query.from_user.id]['awaiting_sender'] = True
    else:
        user_data[callback_query.from_user.id]['sender'] = sender
        await show_status_menu(callback_query)

# Обработка текстового ввода для отправителя
@dp.message_handler(lambda message: message.from_user.id in user_data and user_data[message.from_user.id].get('awaiting_sender'))
async def custom_sender_input(message: types.Message):
    user_data[message.from_user.id]['sender'] = message.text
    user_data[message.from_user.id]['awaiting_sender'] = False
    await show_status_menu(message)

# Меню выбора статуса
async def show_status_menu(callback_query_or_message):
    status_kb = InlineKeyboardMarkup(row_width=2)
    status_kb.add(
        InlineKeyboardButton("Разгружено", callback_data="status_Разгружено"),
        InlineKeyboardButton("Не разгружено", callback_data="status_Не_разгружено"),
        InlineKeyboardButton("Не указано", callback_data="status_Не_указано")
    )
    message = callback_query_or_message.message if isinstance(callback_query_or_message, CallbackQuery) else callback_query_or_message
    await message.edit_text("Выберите статус:", reply_markup=status_kb)

# Выбор статуса
@dp.callback_query_handler(lambda c: c.data.startswith('status_'))
async def status_selected(callback_query: CallbackQuery):
    status = callback_query.data.split('_')[1]
    user_data[callback_query.from_user.id]['status'] = status
    await confirm_selection(callback_query)

# Подтверждение данных
async def confirm_selection(callback_query: CallbackQuery):
    data = user_data[callback_query.from_user.id]
    transport = data['transport']
    cargo = data['cargo']
    sender = data['sender']
    status = data['status']

    confirm_kb = InlineKeyboardMarkup(row_width=2)
    confirm_kb.add(
        InlineKeyboardButton("Подтвердить", callback_data="confirm"),
        InlineKeyboardButton("Отмена", callback_data="cancel")
    )
    await callback_query.message.edit_text(
        f"Подтвердите данные:\n"
        f"Транспортировка: {transport}\n"
        f"Груз: {cargo}\n"
        f"Отправитель: {sender}\n"
        f"Статус: {status}",
        reply_markup=confirm_kb
    )

# Отправка данных в канал и сброс
@dp.callback_query_handler(lambda c: c.data == "confirm")
async def confirm(callback_query: CallbackQuery):
    data = user_data.pop(callback_query.from_user.id, {})
    transport = data['transport']
    cargo = data['cargo']
    sender = data['sender']
    status = data['status']

    await bot.send_message(
        "@precoinmarket_channel",  # Укажите ID вашего канала
        f"Новый заказ:\n"
        f"Транспортировка: {transport}\n"
        f"Груз: {cargo}\n"
        f"Отправитель: {sender}\n"
        f"Статус: {status}"
    )
    await start_command(callback_query.message)

# Отмена и возврат к старту
@dp.callback_query_handler(lambda c: c.data == "cancel")
async def cancel(callback_query: CallbackQuery):
    user_data.pop(callback_query.from_user.id, None)
    await callback_query.message.edit_text("Операция отменена. Начинаем сначала.")
    await start_command(callback_query.message)

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
