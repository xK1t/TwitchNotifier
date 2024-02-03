import asyncio
from aiogram.types import InputFile


async def upload_and_update_file(bot):
    vid = r'/root/TwitchNotifier/Gif/Default.mp4'
    media_message_1 = await bot.send_animation(chat_id=6130068934, animation=InputFile(vid),
                                               caption="Медиа загружены, а их ID сохранён ✅",
                                               disable_notification=True)

    vid_2 = r'/root/TwitchNotifier/Gif/Noty_type.mp4'
    media_message_2 = await bot.send_animation(chat_id=6130068934, animation=InputFile(vid_2),
                                               caption="Медиа загружены, а их ID сохранён ✅",
                                               disable_notification=True)

    vid_3 = r'/root/TwitchNotifier/Gif/Add_streamer.mp4'
    media_message_3 = await bot.send_animation(chat_id=6130068934, animation=InputFile(vid_3),
                                               caption="Медиа загружены, а их ID сохранён ✅",
                                               disable_notification=True)

    vid_4 = r'/root/TwitchNotifier/Gif/Confirm.mp4'
    media_message_4 = await bot.send_animation(chat_id=6130068934, animation=InputFile(vid_4),
                                               caption="Медиа загружены, а их ID сохранён ✅",
                                               disable_notification=True)

    vid_5 = r'/root/TwitchNotifier/Gif/Error.mp4'
    media_message_5 = await bot.send_animation(chat_id=6130068934, animation=InputFile(vid_5),
                                               caption="Медиа загружены, а их ID сохранён ✅",
                                               disable_notification=True)

    with open('file_ids.txt', 'w') as file_id_file:
        file_id_file.write(f"Default_ID: {media_message_1.animation.file_id}\n")
        file_id_file.write(f"Noty_type_ID: {media_message_2.animation.file_id}\n")
        file_id_file.write(f"Personal_message_ID: {media_message_3.animation.file_id}\n")
        file_id_file.write(f"Confirm_ID: {media_message_4.animation.file_id}\n")
        file_id_file.write(f"Error: {media_message_5.animation.file_id}\n")


async def gif(number):
    with open('file_ids.txt', 'r') as vid_id:
        file_contents = vid_id.readlines()
        gif_id = file_contents[number].split(': ')[1].strip()

    return gif_id


async def main(bot):
    interval = 23 * 60 * 60

    while True:
        await upload_and_update_file(bot)
        await asyncio.sleep(interval)


async def type_effect(bot, chat_id, message_id, text, function=None, keyboard=None, delay=0.03):
    current_text = ""
    step = 15

    if function:
        for i in range(0, len(text), step):
            new_text = text[:i + step]
            if new_text != current_text:
                await bot.edit_message_caption(chat_id, message_id, caption=new_text)
                current_text = new_text
            await asyncio.sleep(delay)

        if current_text != text or keyboard:
            await bot.edit_message_caption(chat_id, message_id, caption=text, reply_markup=keyboard)

    else:
        for i in range(0, len(text), step):
            new_text = text[:i + step]
            if new_text != current_text:
                await bot.edit_message_text(new_text, chat_id, message_id, disable_web_page_preview=True)
                current_text = new_text
            await asyncio.sleep(delay)

        if current_text != text or keyboard:
            await bot.edit_message_text(text, chat_id, message_id, reply_markup=keyboard, disable_web_page_preview=True)
