import requests
from dotenv import load_dotenv
import os

import aiohttp

from selenium import webdriver
from bs4 import BeautifulSoup
import time

load_dotenv()
twitch_id = os.getenv('CLIENT_ID')
twitch_key = os.getenv('CLIENT_SECRET')


async def get_twitch_token():
    url = "https://id.twitch.tv/oauth2/token"
    payload = {
        'client_id': twitch_id,
        'client_secret': twitch_key,
        'grant_type': 'client_credentials'
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(url, data=payload) as response:
            response.raise_for_status()
            json_response = await response.json()
            access_token = json_response.get('access_token', None)

            return access_token


async def check_twitch_streamer(username):
    token = await get_twitch_token()

    headers = {"Client-ID": twitch_id, "Authorization": f"Bearer {token}"}
    url = f"https://api.twitch.tv/helix/users?login={username}"

    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as response:
            if response.status == 200:
                data = await response.json()
                return data["data"][0] if data["data"] else None


def get_last_stream_category():
    browser = webdriver.Chrome()

    channel_url = 'https://www.twitch.tv/tiankami'
    browser.get(channel_url)
    time.sleep(5)  # Подождите, чтобы страница полностью загрузилась

    soup = BeautifulSoup(browser.page_source, 'html.parser')
    browser.quit()  # Закрыть браузер после завершения

    # Поиск карточек игр
    game_cards = soup.find_all('div', class_='game-card')
    found_categories = []  # Список для хранения найденных категорий
    for card in game_cards:
        title_element = card.find('h2', class_='CoreText-sc-1txzju1-0')
        if title_element:
            category_title = title_element.get_text(strip=True)
            found_categories.append(category_title)  # Добавляем название категории в список

    if found_categories:
        print("Найденные категории:")
        for category in found_categories:
            print(f"- {category}")
    else:
        print("Не удалось определить категории")
