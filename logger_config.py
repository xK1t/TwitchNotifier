from aiogram import Bot, Dispatcher, types

from message_animations import type_effect
import locale

from dotenv import load_dotenv
import os

import traceback

load_dotenv()

error_bot = Bot(os.getenv('ERROR_BOT_TOKEN'))


def register_error_handler(dp: Dispatcher, bot):
    async def global_error_handler(update: types.Update, exception: Exception):
        # Отправляем сообщение об ошибке в чат
        error_message = f"Произошла ошибка: {exception}"
        await error_bot.send_message(chat_id=116918991, text=error_message, disable_notification=True)

        # Получаем стек вызовов
        traceback_info = traceback.format_exc()

        # Далее вы можете включить traceback_info в сообщение или его часть
        # Например:
        await error_bot.send_message(chat_id=116918991, text=f"Трассировка стека:\n{traceback_info}", disable_notification=True)

        user_id = None
        language_code = 'en'  # Значение по умолчанию
        message_id = None

        if update.message:
            user_id = update.message.from_user.id
            if update.message.from_user.language_code in locale.SUPPORTED_LANGUAGES:
                language_code = update.message.from_user.language_code
        elif update.callback_query:
            user_id = update.callback_query.from_user.id
            if update.callback_query.from_user.language_code in locale.SUPPORTED_LANGUAGES:
                language_code = update.callback_query.from_user.language_code
            message_id = update.callback_query.message.message_id

        if user_id:
            await send_error_message(bot, user_id, language_code, message_id)

    dp.register_errors_handler(global_error_handler, exception=Exception)


async def send_error_message(bot, user_id: int, language_, message_id):
    if message_id:
        temp_message = await bot.edit_message_text(chat_id=user_id, text="...", message_id=message_id)

    else:
        temp_message = await bot.send_message(user_id, "...")

    text = locale.ERROR_MESSAGES.get(language_)
    await type_effect(bot, user_id, temp_message.message_id, text)
