# Функция для отправки сообщения на "Шаг 2: Выбор способа транспортировки"
async def send_transport_choice(user_id):
    # Убедитесь, что все состояния завершены
    state = dp.current_state(chat=user_id, user=user_id)
    await state.reset_state(with_data=False)  # Полностью очищаем состояние перед следующим шагом

    # Создаем клавиатуру для выбора способа транспортировки
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton("🚛Автомобилем", callback_data="transport_auto"),
        InlineKeyboardButton("🚂Вагонами", callback_data="transport_train")
    )
    await bot.send_message(user_id, "Выберите способ транспортировки:", reply_markup=keyboard)

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
        f"🚛Новое поступление🔔\n"
        f"_______\n"
        f"Транспортировка: {transport}\n"
        f"Груз: {cargo}\n"
        f"Отправитель: {sender}\n"
    )
    if transport == "🚛Автомобилем":
        message += f"Количество машин: {quantity}\n"
    elif transport == "🚂Вагонами":
        message += f"Статус: {status}\n"

    await bot.send_message(CHANNEL_ID, message)
    await callback_query.answer("Данные успешно отправлены!")

    # Возвращаемся к выбору транспортировки
    await send_transport_choice(callback_query.from_user.id)

# Шаг 8: Отмена
@dp.callback_query_handler(lambda c: c.data == "cancel")
async def cancel_handler(callback_query: CallbackQuery):
    user_data.pop(callback_query.from_user.id, None)
    await callback_query.answer("Операция отменена.")
    await send_transport_choice(callback_query.from_user.id)
