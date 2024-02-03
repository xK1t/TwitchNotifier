from openai import OpenAI

from dotenv import load_dotenv
import os

import json
from datetime import datetime

import localization as locale

load_dotenv()
GPT = os.getenv('GPT_TOKEN')


def log_conversation(user_id):
    if not os.path.exists('logs'):
        os.makedirs('logs')

    # Получаем объект памяти для данного пользователя
    if user_id in user_memories:
        user_memory = user_memories[user_id].get_memory()

        # Формируем имя файла из user_id
        filename = f"logs/{user_id}.json"

        # Записываем данные в файл. Добавляем дату и время к каждому логу для удобства отслеживания.
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump({"user_id": user_id, "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                       "messages": user_memory}, f, ensure_ascii=False, indent=4)

        # Опционально: можно очистить память после логирования, если это необходимо
        # clear_user_memory(user_id)


class ChatMemory:
    def __init__(self):
        self.messages = []

    def add_message(self, role, content):
        self.messages.append({"role": role, "content": content})

    def get_memory(self):
        return self.messages

    def clear_memory(self):
        self.messages = []


# Объявите объекты памяти для каждого пользователя
user_memories = {}


# Создайте функцию, которая вызывает GPT-3.5 с заданным запросом
def get_gpt_response(query, user_id, language_code):
    if user_id not in user_memories:
        user_memories[user_id] = ChatMemory()

    user_memory = user_memories[user_id]

    client = OpenAI(api_key=GPT)

    system_text = locale.GPT_MODEL.get(language_code, "default value").format(language_code=language_code)

    messages = user_memory.get_memory()  # добавляю предыдущее сообщение к текущему
    messages.append({"role": "user", "content": query})

    response = client.chat.completions.create(
        model="gpt-4-1106-preview",
        messages=[
                     {
                         "role": "system",
                         "content": system_text
                     }
                 ] + messages,
        temperature=1,
        max_tokens=300,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0
    )

    user_memory.add_message("assistant", response.choices[0].message.content)  # сохраняю новое сообщение в память

    response_content = response.choices[0].message.content

    # Логирование разговора
    log_conversation(user_id)

    return response_content


def clear_user_memory(user_id):
    if user_id in user_memories:
        user_memories[user_id].clear_memory()