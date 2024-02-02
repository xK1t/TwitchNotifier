from dotenv import load_dotenv
import os

import aiohttp

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
            json_response = await response.json()  # Дожидаемся выполнения асинхронной операции
            access_token = json_response.get('access_token', None)  # Получаем access_token безопасным способом
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

    return None


async def get_streamer_streams(username):
    user_info = await check_twitch_streamer(username)
    if user_info:
        user_id = user_info['id']
        url = f"https://api.twitch.tv/helix/streams?user_id={user_id}"

        headers = {"Client-ID": twitch_id, "Authorization": f"Bearer {await get_twitch_token()}"}

        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    print(data["data"])  # Список стримов, включая информацию о категориях
    print(data["data"])


async def get_streamer_games(username):
    user_info = await check_twitch_streamer(username)
    if user_info:
        user_id = user_info['id']
        videos_url = f"https://api.twitch.tv/helix/videos?user_id={user_id}"

        headers = {"Client-ID": twitch_id, "Authorization": f"Bearer {await get_twitch_token()}"}

        game_ids = set()
        async with aiohttp.ClientSession() as session:
            async with session.get(videos_url, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    for video in data["data"]:
                        if "game_id" in video and video["game_id"]:
                            game_ids.add(video["game_id"])
                else:
                    print("Error fetching videos:", response.status)

        # Получение названий игр
        games = {}
        for game_id in game_ids:
            games_url = f"https://api.twitch.tv/helix/games?id={game_id}"
            async with session.get(games_url, headers=headers) as response:
                if response.status == 200:
                    game_data = await response.json()
                    games[game_id] = game_data["data"][0]["name"] if game_data["data"] else "Unknown Game"

        print(games)
    else:
        print(f"Streamer {username} not found or unable to retrieve user info.")


