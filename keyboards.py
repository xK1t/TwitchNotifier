from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.dispatcher import FSMContext
from aiogram import types

import localization as locale
import database as db
import state_object
import gpt


def register_keyboard_handlers(bot, dp, language_selection, send_default_message, where_to_send_notifications,
                               personal_messages):
    async def confirm_language_yes(callback_query: types.CallbackQuery):
        """Подтверждение автоматического языка"""
        check_streamer = await db.get_user_info(callback_query.from_user)
        lang_code = callback_query.data.split('_')[3]

        if check_streamer:
            await send_default_message(callback_query, lang_code, check_streamer[5])
        else:
            await send_default_message(callback_query, lang_code)

    async def confirm_language_no(callback_query: types.CallbackQuery):
        """Выбор языка в ручную"""
        user_info = await db.get_user_info(callback_query.from_user)
        if user_info:
            language_code = user_info[4]
            await language_selection(callback_query, language_code)

    async def set_language(callback_query: types.CallbackQuery):
        """Ручная настройка языка"""
        lang_code = callback_query.data.split('_')[2]
        await db.update_language_code(callback_query.from_user.id, lang_code)

        user_info = await db.get_user_info(callback_query.from_user)

        await bot.answer_callback_query(callback_query.id, text=locale.LANGUAGE_UPDATE.get(user_info[4]))

        if user_info[5]:
            await send_default_message(callback_query, user_info[4], user_info[5])
        else:
            await send_default_message(callback_query, user_info[4])

    async def add_streamer_button(callback_query: types.CallbackQuery, state: FSMContext):
        """Переход к добавлению стримера"""
        user_info = await db.get_user_info(callback_query.from_user)
        if user_info:
            language_code = user_info[4]
            await where_to_send_notifications(callback_query, language_code)

        await state.reset_state()

    async def back_to_default(callback_query: types.CallbackQuery):
        """Возврат к стандартному сообщению"""
        user_info = await db.get_user_info(callback_query.from_user)

        if user_info:
            await send_default_message(callback_query, user_info[4], user_info[5])
        else:
            await send_default_message(callback_query, user_info[4])

    async def stop_gpt(callback_query: types.CallbackQuery, state: FSMContext):
        """Возврат к стандартному сообщению после чата с GPT"""
        user_info = await db.get_user_info(callback_query.from_user)

        if user_info:
            await send_default_message(callback_query, user_info[4], user_info[5])
        else:
            await send_default_message(callback_query, user_info[4])

        gpt.clear_user_memory(callback_query.from_user.id)

        await state.reset_state()

    async def personal_messages_button(callback_query: types.CallbackQuery, state: FSMContext):
        """Подписка на уведомления в личные сообщения"""
        user_info = await db.get_user_info(callback_query.from_user)

        await personal_messages(callback_query, user_info[4], state)

    dp.register_callback_query_handler(confirm_language_yes,
                                       lambda c: c.data.startswith('confirm_language_yes'))
    dp.register_callback_query_handler(confirm_language_no,
                                       lambda c: c.data.startswith('confirm_language_no'))
    dp.register_callback_query_handler(set_language,
                                       lambda c: c.data.startswith('set_language'))
    dp.register_callback_query_handler(add_streamer_button,
                                       lambda c: c.data.startswith('add_streamer'))
    dp.register_callback_query_handler(stop_gpt,
                                       lambda c: c.data.startswith('stop'), state=state_object.GPT_CHAT)
    dp.register_callback_query_handler(back_to_default,
                                       lambda c: c.data.startswith('back_to_default'))
    dp.register_callback_query_handler(personal_messages_button,
                                       lambda c: c.data.startswith('personal_messages'))
    dp.register_callback_query_handler(add_streamer_button,
                                       lambda c: c.data.startswith('back_to_notice_type'),
                                       state=state_object.WAITING_FOR_STREAMER_NAME)


def language_keyboard():
    """Клавиатура с поддерживаемыми языками"""
    keyboard = InlineKeyboardMarkup(row_width=1)

    for lang_code, lang_name in locale.SUPPORTED_LANGUAGES.items():
        keyboard.add(InlineKeyboardButton(lang_name, callback_data=f"set_language_{lang_code}"))

    return keyboard


def confirm_language_keyboard(language_code):
    """Клавиатура для подтверждения автоматического языка"""
    buttons = locale.LANGUAGE_CONFIRMATION_BUTTONS.get(language_code)

    keyboard = InlineKeyboardMarkup()

    keyboard.row(InlineKeyboardButton(buttons["yes"], callback_data=f"confirm_language_yes_{language_code}"),
                 InlineKeyboardButton(buttons["no"], callback_data=f"confirm_language_no_{language_code}"))

    return keyboard


def default_keyboard(check_streamer, language_code):
    """Клавиатура для стандартного сообщения"""
    keyboard = InlineKeyboardMarkup(row_width=1)
    add_streamer = locale.ADD_STREAMER_BUTTONS.get(language_code)
    follow_list = locale.FOLLOW_LIST.get(language_code)

    if check_streamer:
        keyboard.add(InlineKeyboardButton(add_streamer, callback_data='add_streamer'),
                     InlineKeyboardButton(follow_list, callback_data='follow_list'))

    else:
        keyboard.add(InlineKeyboardButton(add_streamer, callback_data='add_streamer'))

    return keyboard


def notice_type_keyboard(language_code):
    """Клавиатура для выбора типа уведомлений"""
    keyboard = InlineKeyboardMarkup(row_width=1)
    personal_messages = locale.PERSONAL_MESSAGES.get(language_code)
    channel = locale.CHANNEL.get(language_code)
    back = back_to_default_keyboard(language_code)

    keyboard.add(InlineKeyboardButton(personal_messages, callback_data='personal_messages'),
                 InlineKeyboardButton(channel, callback_data='channel'),
                 back)

    return keyboard


def stop_keyboard(language_code):
    """Клавиатура для остановки GPT"""
    keyboard = InlineKeyboardMarkup()
    button = locale.STOP_BUTTONS.get(language_code)

    keyboard.add(InlineKeyboardButton(button, callback_data='stop'))

    return keyboard


def finish_keyboard(language_code):
    """Клавиатура после остановки чата"""
    keyboard = InlineKeyboardMarkup()
    button = locale.FINISH_BUTTONS.get(language_code)

    keyboard.add(InlineKeyboardButton(button, callback_data='finish'))

    return keyboard


def back_to_default_keyboard(language_code):
    """Кнопка 'Назад' к стандартному сообщению"""
    button_text = locale.BACK_TO_START_BUTTON.get(language_code)

    button = InlineKeyboardButton(button_text, callback_data='back_to_default')

    return button


def back_to_notice_type_keyboard(language_code):
    """Кнопка 'Назад' к выбору типа уведомлений"""
    keyboard = InlineKeyboardMarkup()
    button_text = locale.BACK_BUTTON.get(language_code)

    keyboard.add(InlineKeyboardButton(button_text, callback_data='back_to_notice_type'))

    return keyboard


def add_streamer_final(language_code):
    keyboard = InlineKeyboardMarkup(row_width=1)

    follow_list = locale.FOLLOW_LIST.get(language_code)
    add_streamer = locale.ADD_STREAMER_BUTTONS.get(language_code)
    back = back_to_default_keyboard(language_code)

    keyboard.add(InlineKeyboardButton(add_streamer, callback_data='add_streamer'),
                 InlineKeyboardButton(follow_list, callback_data='follow_list'),
                 back)

    return keyboard
