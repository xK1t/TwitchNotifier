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
