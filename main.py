import asyncio

from aiogram.types import InputMediaAnimation
from dotenv import load_dotenv
import os
import re

from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext

import database as db
import localization as locale
import message_animations as ani
import logger_config
import keyboards
import gpt
import state_object
import twitch

load_dotenv()

bot = Bot(os.getenv('BOT_TOKEN'))
dp = Dispatcher(bot, storage=MemoryStorage())


async def on_startup(_dp):
    await db.init_database()  # инициализация базы данных при запуске бота


@dp.message_handler(commands=["start"])
async def start(message: types.Message):
    """Обработчик команды /start"""

    user = message.from_user

    existing_user = await db.get_user_info(user)

    if existing_user:  # если юзер есть в базе данных

        if existing_user[4] and user.language_code in locale.SUPPORTED_LANGUAGES:  # если сохранен языковой код и он поддерживается
            await send_default_message(message, existing_user[4], existing_user[5])
        else:  # если не сохранён языковой код
            await language_selection(message, user.language_code)

    else:
        if user.language_code not in locale.SUPPORTED_LANGUAGES:  # если новый юзер и бот не поддерживает языковой код
            await db.add_user(user.id, user.first_name, user.last_name, user.username, user.language_code)

            await language_selection(message, user.language_code)
        else:  # если новый юзер и бот поддерживает языковой код
            await db.add_user(user.id, user.first_name, user.last_name, user.username, user.language_code)

            await confirm_language(message, user.language_code)


@dp.message_handler(commands=["language"])
async def language(message: types.Message):
    """Обрабатывает команду /language"""

    user = message.from_user
    user_info = await get_or_create_user(user, user.first_name, user.last_name, user.username, user.language_code)

    if user_info:
        language_code = user_info[4]
        await language_selection(message, language_code)


@dp.message_handler(commands=["chat"])
async def chat_cmd(message: types.Message, state: FSMContext):
    """Обработка команды /chat"""

    await state.set_state(state_object.GPT_CHAT)

    await gpt_chat(message)


@dp.message_handler(state=state_object.GPT_CHAT, content_types=['text'])
async def gpt_chat(message: types.Message):
    """Обработчик сообщений для GPT"""
    user = message.from_user
    user_text = message.text

    user_info = await db.get_user_info(user)

    bot_typing = await bot.send_chat_action(chat_id=message.from_user.id, action='typing')
    gpt_text = gpt.get_gpt_response(user_text, user.id, user_info[4])

    keyboard = keyboards.stop_keyboard(user_info[4])

    temp_message = await bot.send_message(message.from_user.id, '...')
    await ani.type_effect(bot, message.from_user.id, temp_message.message_id, gpt_text, keyboard=keyboard)


async def confirm_language(message, language_code_from_tg):
    """Подтверждение языка"""

    text = locale.LANGUAGE_CONFIRMATION.get(language_code_from_tg)

    keyboard = keyboards.confirm_language_keyboard(language_code_from_tg)
    temp_message = await bot.send_message(message.from_user.id, "...")

    await ani.type_effect(bot, message.from_user.id, temp_message.message_id, text, keyboard=keyboard)


async def get_or_create_user(user, first_name=None, last_name=None, username=None, language_code=None):
    """Получает информацию о пользователе из БД или создает новую запись, если не найдено."""

    user_info = await db.get_user_info(user)

    if not user_info:
        await db.add_user(user.id, first_name, last_name, username, language_code)
        user_info = await db.get_user_info(user.id)

    return user_info


async def send_default_message(user, language_code, check_streamer=None):
    """Отправляет приветственное сообщение"""
    language_text = locale.LANGUAGE_HELLO.get(language_code)

    keyboard = keyboards.default_keyboard(check_streamer, language_code)

    gif_id = await ani.gif(0)

    if isinstance(user, types.CallbackQuery):

        if user.data != 'stop':
            await bot.delete_message(user.from_user.id, user.message.message_id)
        else:
            await bot.edit_message_text(user.message.text, user.from_user.id, user.message.message_id,
                                        reply_markup=keyboards.finish_keyboard(language_code))

        temp_message = await bot.send_animation(user.from_user.id, gif_id, caption='...')

        await ani.type_effect(bot, user.from_user.id, temp_message.message_id, language_text,
                              'send_default_message', keyboard)
    else:
        temp_message = await bot.send_animation(user.chat.id, gif_id, caption='...')

        await ani.type_effect(bot, user.chat.id, temp_message.message_id, language_text,
                              'send_default_message', keyboard)


async def language_selection(user, language_code):
    """Отправляет сообщение с выбором языка"""

    keyboard = keyboards.language_keyboard()
    text = locale.LANGUAGE_SELECTION.get(language_code, locale.LANGUAGE_SELECTION['kit'])

    if isinstance(user, types.CallbackQuery):
        temp_message = await bot.edit_message_text("...", user.from_user.id, user.message.message_id)
        await ani.type_effect(bot, user.from_user.id, temp_message.message_id, text, keyboard=keyboard)

    else:
        temp_message = await user.answer("...")
        await ani.type_effect(bot, user.from_user.id, temp_message.message_id, text, keyboard=keyboard)


async def where_to_send_notifications(user, language_code):
    """Выбор типа уведомлений"""

    keyboard = keyboards.notice_type_keyboard(language_code)
    text = locale.SELECTING_A_NOTIFICATION_TYPE.get(language_code)

    gif_id = await ani.gif(1)

    if isinstance(user, types.CallbackQuery):
        temp_message = await bot.edit_message_media(InputMediaAnimation(gif_id), user.from_user.id,
                                                    user.message.message_id)

        await ani.type_effect(bot, user.from_user.id, temp_message.message_id, text,
                              'where_to_send_notifications', keyboard)
    else:
        temp_message = await bot.send_animation(user.chat.id, gif_id, caption='...')

        await ani.type_effect(bot, user.chat.id, temp_message.message_id, text,
                              'where_to_send_notifications', keyboard)


async def personal_messages(user, language_code, state: FSMContext):
    """Личные сообщения"""

    keyboard = keyboards.back_to_notice_type_keyboard(language_code)
    text = locale.GIVE_STREAMER_NAME.get(language_code)

    gif_id = await ani.gif(2)

    temp_message = await bot.edit_message_media(InputMediaAnimation(gif_id), user.from_user.id,
                                                user.message.message_id)

    await ani.type_effect(bot, user.from_user.id, temp_message.message_id, text,
                          'personal_messages', keyboard)

    await state.set_state(state_object.WAITING_FOR_STREAMER_NAME)


@dp.message_handler(state=state_object.WAITING_FOR_STREAMER_NAME, content_types=['text'])
async def handler_username(message: types.Message, state: FSMContext):
    user = message.from_user
    user_id = user.id
    input_text = message.text.lower()

    user_info = await db.get_user_info(user)

    match = re.match(r"(?:https?://)?(?:www\.)?twitch\.tv/([a-zA-Z0-9_]+)", input_text)
    username = match.group(1) if match else input_text

    gif_id = await ani.gif(3)
    add_streamer_result = await db.add_streamer(user_id, username)
    keyboard = keyboards.add_streamer_final(user_info[4])

    if add_streamer_result == 1:
        language_text = locale.STREAMER_TRACKING_CONFIRMATION[user_info[4]].format(username=username)

        temp_message = await bot.send_animation(user.id, gif_id, caption='...')
        await ani.type_effect(bot, user.id, temp_message.message_id, language_text,
                              'handler_username', keyboard)

    elif add_streamer_result == 2:
        language_text = locale.ALREADY_TRACKING_MESSAGE[user_info[4]].format(username=username)

        temp_message = await bot.send_animation(user.id, gif_id, caption='...')

        await ani.type_effect(bot, user.id, temp_message.message_id, language_text,
                              'handler_username', keyboard)

    elif add_streamer_result == 0:
        language_text = locale.STREAMER_NOT_FOUND_MESSAGE[user_info[4]].format(username=username)

        temp_message = await bot.send_animation(user.id, await ani.gif(4), caption='...')

        await ani.type_effect(bot, user.id, temp_message.message_id, language_text,
                              'handler_username', keyboard)

    await state.reset_state()


if __name__ == "__main__":
    print('запущено!!!!!!!!!')
    keyboards.register_keyboard_handlers(bot, dp, language_selection, send_default_message, where_to_send_notifications,
                                         personal_messages)
    logger_config.register_error_handler(dp, bot)

    twitch.get_last_stream_category()

    loop = asyncio.get_event_loop()
    loop.create_task(ani.main(bot))

    executor.start_polling(dp, skip_updates=True, on_startup=on_startup)
