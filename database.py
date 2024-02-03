import aiosqlite
import twitch

DB_PATH = 'Notifier.db'


async def init_database():
    conn = await aiosqlite.connect(DB_PATH)
    cursor = await conn.cursor()
    table_users = """
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        first_name TEXT,
        last_name TEXT,
        username TEXT,
        language_code TEXT,
        streamers TEXT)"""
    table_streamers = """
    CREATE TABLE IF NOT EXISTS streamers (
        streamer TEXT PRIMARY KEY,
        user_id INTEGER, 
        status TEXT, 
        notified TEXT)"""
    await cursor.execute(table_users)
    await cursor.execute(table_streamers)
    await conn.commit()
    await cursor.close()
    await conn.close()


async def add_user(user_id, first_name, last_name, username, language_code):
    async with aiosqlite.connect(DB_PATH) as conn, conn.cursor() as cursor:
        query = """
            INSERT INTO users (user_id, first_name, last_name, username, language_code)
            VALUES (?, ?, ?, ?, ?)"""
        await cursor.execute(query, (user_id, first_name, last_name, username, language_code))
        await conn.commit()


async def add_streamer(user_id, username):
    result = 0

    if await twitch.check_twitch_streamer(username):

        async with aiosqlite.connect(DB_PATH) as conn:
            async with conn.cursor() as cursor:
                # Добавляем запись в таблицу streamers
                await cursor.execute("SELECT streamer, user_id FROM streamers WHERE streamer = ?", (username,))
                result = await cursor.fetchone()
                if result is None:
                    await cursor.execute("INSERT INTO streamers (streamer, user_id, status, notified) VALUES (?, ?, ?, ?)",
                                         (username, user_id, "offline", "NO"))
                else:
                    _, user = result
                    if str(user) and str(user_id) not in str(user):
                        await cursor.execute("UPDATE streamers SET user_id = user_id || ? WHERE streamer = ?",
                                             (',' + str(user_id), username))
                    elif not user:
                        await cursor.execute("UPDATE streamers SET user_id = ? WHERE streamer = ?", (user_id, username))

            async with conn.cursor() as cursor:

                # Добавляем запись в таблицу users
                await cursor.execute("SELECT user_id, streamers FROM users WHERE user_id = ?", (user_id,))
                data = await cursor.fetchone()

                if data is None:
                    result = 1
                    await cursor.execute("INSERT INTO users (user_id, streamers) VALUES (?, ?)", (user_id, username))

                else:
                    _, streamer = data

                    if streamer and username not in streamer:
                        result = 1
                        await cursor.execute("UPDATE users SET streamers = streamers || ? WHERE user_id = ?",
                                             (',' + username, user_id))

                    elif not streamer:
                        result = 1
                        await cursor.execute("UPDATE users SET streamers = ? WHERE user_id = ?", (username, user_id))

                    else:
                        result = 2

            await conn.commit()
    return result


async def update_language_code(user_id, new_language_code):
    async with aiosqlite.connect(DB_PATH) as conn, conn.cursor() as cursor:
        query = """
            UPDATE users
            SET language_code = ?
            WHERE user_id = ?"""
        await cursor.execute(query, (new_language_code, user_id))
        await conn.commit()


async def get_user_info(user):
    async with aiosqlite.connect(DB_PATH) as conn, conn.cursor() as cursor:
        query = "SELECT * FROM users WHERE user_id = ?"

        if await cursor.execute(query, (user.id,)):
            return await cursor.fetchone()

        else:
            return user.language_code
