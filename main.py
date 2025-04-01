import asyncio
from aiogram import Dispatcher, Bot
from config import TOKEN
from db import SQLiteService
from google_sheets import SheetsService
from handlers import TelegramRouter
from services.news import NewsService
from services.start import StartService
from utils import logger


async def main():
    import os
    
    # Check for running instance
    if os.path.exists("bot.lock"):
        logger.error("Bot is already running! If not, delete bot.lock file.")
        return
        
    # Create lock file
    with open("bot.lock", "w") as f:
        f.write(str(os.getpid()))
        
    try:
        # Initialize bot and dispatcher
        bot = Bot(token=TOKEN)

    # Delete webhook before starting polling
    await bot.delete_webhook()

    dp = Dispatcher()  # No storage needed since we're not using FSM

    # Initialize services
    sheets_service = SheetsService()
    sqlite_service = SQLiteService(db_path="nodepressionbot.db")
    start_service = StartService(sheets_service, sqlite_service)
    news_service = NewsService(bot, sheets_service)

    # Initialize router
    telegram_router = TelegramRouter(bot, start_service, news_service, sheets_service)

    # Register router
    dp.include_router(telegram_router.router)

    # Start polling
    logger.info("Starting bot")
    await dp.start_polling(bot, skip_updates=True)
    finally:
        # Clean up lock file
        if os.path.exists("bot.lock"):
            os.remove("bot.lock")


if __name__ == "__main__":
    asyncio.run(main())