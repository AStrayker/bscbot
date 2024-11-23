import os
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils import executor
from aiogram.dispatcher import FSMContext
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.dispatcher.storage import MemoryStorage

# Бот и диспетчер
BOT_TOKEN = os.getenv("6072615655:AAHQh3BVU3HNHd3p7vfvE3JsBzfHiG-hNMU")
bot = Bot(token=6072615655:AAHQh3BVU3HNHd3p7vfvE3JsBzfHiG-hNMU)
dp = Dispatcher(bot, storage=MemoryStorage())
dp.middleware.setup(LoggingMiddleware())

# Состояния
class OrderState(StatesGroup):
    waiting_for_cargo = State()
    waiting_for_sender = State()
    waiting_for_quantity = State()
    waiting_for_confirmation = State()
    editing_message = State()
    editing_choice = State()

# Фиктивные пользователи для отправки в ЛС
PRIVATE_RECIPIENTS = [282198872, 2037127199]  # Замените ID на реальные

# Кнопки
def start_keyboard():
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(InlineKeyboardButton("Металлопрокат", callback_data="cargo_metal"))
    keyboard.add(InlineKeyboardButton("Отмена", callback_data="cancel"))
    return keyboard

def confirm_keyboard():
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(InlineKeyboardButton("Подтвердить", callback_data="confirm"))
    keyboard.add(InlineKeyboardButton("Редактировать", callback_data="edit"))
    keyboard.add(InlineKeyboardButton("Отмена", callback_data="cancel"))
    return keyboard

def quantity_keyboard():
    keyboard = InlineKeyboardMarkup(row_width=3)
    for i in range(1, 6):
        keyboard.insert(InlineKeyboardButton(str(i), callback_data=f"quantity_{i}"))
    keyboard.add(InlineKeyboardButton("Ввести вручную", callback_data="manual_quantity"))
    keyboard.add(InlineKeyboardButton("Отмена", callback_data="cancel"))
    return keyboard

def edit_keyboard():
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton("Изменить груз", callback_data="edit_cargo"),
        InlineKeyboardButton("Изменить отправителя", callback_data="edit_sender"),
        InlineKeyboardButton("Изменить количество", callback_data="edit_quantity"),
    )
    keyboard.add(InlineKeyboardButton("Не редактировать", callback_data="edit_cancel"))
    return keyboard

# Хендлеры
@dp.message_handler(commands="start", state="*")
async def start_command(message: types.Message, state: FSMContext):
    await state.finish()  # Сбрасываем состояние
    await message.answer("Выберите груз:", reply_markup=start_keyboard())
    await OrderState.waiting_for_cargo.set()

@dp.callback_query_handler(lambda c: c.data == "cancel", state="*")
async def cancel_order(callback_query: types.CallbackQuery, state: FSMContext):
    await state.finish()  # Сбрасываем состояние
    await callback_query.message.edit_text("Действие отменено. Начните сначала с команды /start.")
    await start_command(callback_query.message, state)

@dp.callback_query_handler(lambda c: c.data == "cargo_metal", state=OrderState.waiting_for_cargo)
async def select_sender(callback_query: types.CallbackQuery, state: FSMContext):
    await state.update_data(cargo="Металлопрокат")
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton("Викант", callback_data="sender_vikant"),
        InlineKeyboardButton("Вартис", callback_data="sender_vartis"),
        InlineKeyboardButton("АВ Металл Групп", callback_data="sender_av"),
        InlineKeyboardButton("Парк Плюс", callback_data="sender_park"),
    )
    keyboard.add(InlineKeyboardButton("Назад", callback_data="cancel"))
    await callback_query.message.edit_text("Выберите отправителя:", reply_markup=keyboard)
    await OrderState.waiting_for_sender.set()

@dp.callback_query_handler(lambda c: c.data.startswith("sender_"), state=OrderState.waiting_for_sender)
async def select_quantity(callback_query: types.CallbackQuery, state: FSMContext):
    sender = callback_query.data.split("_")[1].capitalize()
    await state.update_data(sender=sender)
    await callback_query.message.edit_text("Выберите количество машин:", reply_markup=quantity_keyboard())
    await OrderState.waiting_for_quantity.set()

@dp.callback_query_handler(lambda c: c.data.startswith("quantity_"), state=OrderState.waiting_for_quantity)
async def confirm_order(callback_query: types.CallbackQuery, state: FSMContext):
    quantity = int(callback_query.data.split("_")[1])
    await state.update_data(quantity=quantity)
    data = await state.get_data()
    message_text = (
        f"Груз: {data['cargo']}\n"
        f"Отправитель: {data['sender']}\n"
        f"Количество: {data['quantity']}"
    )
    await callback_query.message.edit_text(message_text, reply_markup=confirm_keyboard())
    await OrderState.waiting_for_confirmation.set()

@dp.callback_query_handler(lambda c: c.data == "confirm", state=OrderState.waiting_for_confirmation)
async def send_order(callback_query: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    message_text = (
        f"Груз: {data['cargo']}\n"
        f"Отправитель: {data['sender']}\n"
        f"Количество: {data['quantity']}"
    )
    # Логика отправки в ЛС или канал
    if data['cargo'] == "Металлопрокат":
        for user_id in PRIVATE_RECIPIENTS:
            await bot.send_message(user_id, message_text)
    else:
        await bot.send_message(-1001820926878, message_text)  # ID вашего канала
    await callback_query.message.edit_text("Сообщение отправлено!")
    await start_command(callback_query.message, state)

@dp.callback_query_handler(lambda c: c.data == "edit", state=OrderState.waiting_for_confirmation)
async def edit_order(callback_query: types.CallbackQuery, state: FSMContext):
    await callback_query.message.edit_text("Что вы хотите изменить?", reply_markup=edit_keyboard())
    await OrderState.editing_choice.set()

@dp.callback_query_handler(lambda c: c.data.startswith("edit_"), state=OrderState.editing_choice)
async def edit_choice(callback_query: types.CallbackQuery, state: FSMContext):
    choice = callback_query.data.split("_")[1]
    if choice == "cancel":
        await confirm_order(callback_query, state)
        return
    elif choice == "cargo":
        await start_command(callback_query.message, state)
    elif choice == "sender":
        await select_sender(callback_query, state)
    elif choice == "quantity":
        await select_quantity(callback_query, state)

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
