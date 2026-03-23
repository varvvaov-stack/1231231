import asyncio
import logging
from aiogram import Bot, Dispatcher
from config import TOKEN
from database import init_db
import handlers

async def main():
    logging.basicConfig(level=logging.INFO)
    bot = Bot(token=TOKEN)
    handlers.bot = bot
    dp = Dispatcher()
    dp.include_router(handlers.router)
    await init_db()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())