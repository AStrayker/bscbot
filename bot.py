# Подтверждение или отмена
@dp.callback_query_handler(lambda c: c.data == "confirm")
async def confirm_handler(callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    data = user_data.pop(user_id, {})  # Удаляем данные после отправки
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

    await bot.send_message(CHANNEL_ID, message)
    await callback_query.answer("Данные отправлены в канал!")

    # Завершаем текущий процесс и начинаем новый шаг выбора транспорта
    await bot.send_message(user_id, "Возвращаемся к выбору способа транспортировки.")
    
    # Очистим FSM контекст
    await OrderState.choosing_quantity.finish()
    await OrderState.choosing_status.finish()

    # Возврат на начало: Шаг 1 (выбор транспорта)
    keyboard = InlineKeyboardMarkup(row_width=2).add(
        InlineKeyboardButton("🚛Автомобилем", callback_data="transport_auto"),
        InlineKeyboardButton("🚂Вагонами", callback_data="transport_train")
    )
    await send_message_with_keyboard(user_id, "Выберите способ транспортировки:", keyboard)

@dp.callback_query_handler(lambda c: c.data == "cancel")
async def cancel_handler(callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    # Очистим данные пользователя перед возвратом
    if user_id in user_data:
        del user_data[user_id]
    
    await callback_query.answer("Операция отменена.")
    # Очистим FSM контекст
    await OrderState.choosing_quantity.finish()
    await OrderState.choosing_status.finish()

    # Перезапуск с выбора транспортировки (Шаг 2)
    keyboard = InlineKeyboardMarkup(row_width=2).add(
        InlineKeyboardButton("🚛Автомобилем", callback_data="transport_auto"),
        InlineKeyboardButton("🚂Вагонами", callback_data="transport_train")
    )
    await send_message_with_keyboard(callback_query.from_user.id, "Выберите способ транспортировки:", keyboard)
