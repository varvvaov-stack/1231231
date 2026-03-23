import sqlite3
import aiosqlite
from datetime import datetime

DB_PATH = "bot.db"

async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                date_registration TEXT,
                is_admin INTEGER DEFAULT 0
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS photos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                file_id TEXT,
                timestamp TEXT,
                FOREIGN KEY(user_id) REFERENCES users(user_id)
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS help_requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                text TEXT,
                timestamp TEXT,
                answered INTEGER DEFAULT 0,
                answer_text TEXT,
                FOREIGN KEY(user_id) REFERENCES users(user_id)
            )
        """)
        await db.commit()

# Добавление/обновление пользователя
async def add_user(user_id, username, first_name):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT OR IGNORE INTO users (user_id, username, first_name, date_registration, is_admin)
            VALUES (?, ?, ?, ?, ?)
        """, (user_id, username, first_name, datetime.now().isoformat(), 0))
        await db.commit()

# Проверка существования пользователя
async def user_exists(user_id):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT 1 FROM users WHERE user_id = ?", (user_id,)) as cursor:
            return await cursor.fetchone() is not None

# Получение всех пользователей
async def get_all_users():
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT user_id FROM users") as cursor:
            return [row[0] for row in await cursor.fetchall()]

# Получение профиля
async def get_user_profile(user_id):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("""
            SELECT u.user_id, u.username, u.first_name, u.date_registration,
                   (SELECT COUNT(*) FROM help_requests WHERE user_id = u.user_id) as help_count
            FROM users u
            WHERE u.user_id = ?
        """, (user_id,)) as cursor:
            row = await cursor.fetchone()
            if row:
                return {
                    "user_id": row[0],
                    "username": row[1],
                    "first_name": row[2],
                    "date_registration": row[3],
                    "help_count": row[4]
                }
    return None

# Добавление фото
async def add_photo(user_id, file_id):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT INTO photos (user_id, file_id, timestamp)
            VALUES (?, ?, ?)
        """, (user_id, file_id, datetime.now().isoformat()))
        await db.commit()

# Получение всех фото
async def get_all_photos():
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("""
            SELECT p.user_id, p.file_id, p.timestamp, u.username
            FROM photos p
            JOIN users u ON p.user_id = u.user_id
            ORDER BY p.timestamp DESC
        """) as cursor:
            return await cursor.fetchall()

# Добавление обращения в помощь
async def add_help_request(user_id, text):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT INTO help_requests (user_id, text, timestamp)
            VALUES (?, ?, ?)
        """, (user_id, text, datetime.now().isoformat()))
        await db.commit()

# Получение всех неотвеченных обращений
async def get_unanswered_help_requests():
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("""
            SELECT h.id, h.user_id, h.text, h.timestamp, u.username
            FROM help_requests h
            JOIN users u ON h.user_id = u.user_id
            WHERE h.answered = 0
            ORDER BY h.timestamp DESC
        """) as cursor:
            return await cursor.fetchall()

# Ответ на обращение
async def answer_help_request(request_id, answer_text):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            UPDATE help_requests
            SET answered = 1, answer_text = ?
            WHERE id = ?
        """, (answer_text, request_id))
        await db.commit()

# Получение пользователя по username (для выдачи админки)
async def get_user_by_username(username):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT user_id FROM users WHERE username = ?", (username,)) as cursor:
            row = await cursor.fetchone()
            return row[0] if row else None

# Сделать пользователя админом
async def set_admin(user_id):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE users SET is_admin = 1 WHERE user_id = ?", (user_id,))
        await db.commit()

# Проверка, является ли пользователь админом
async def is_admin(user_id):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT is_admin FROM users WHERE user_id = ?", (user_id,)) as cursor:
            row = await cursor.fetchone()
            return row and row[0] == 1