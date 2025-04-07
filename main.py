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
    try:
        import os
        
        # Check for lock file
        if os.path.exists("bot.lock"):
            logger.error("Bot is already running! If not, delete bot.lock file.")
            return
            
        # Create lock file
        with open("bot.lock", "w") as f:
            f.write(str(os.getpid()))
            
        # Initialize bot and dispatcher
        bot = Bot(token=TOKEN)

        # Delete webhook and wait a bit to ensure clean state
        await bot.delete_webhook(drop_pending_updates=True)
        await asyncio.sleep(1)

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
    except Exception as e:
        logger.error(f"Critical error: {e}")
        raise
    finally:
        logger.info("Shutting down bot")
        if 'bot' in locals():
            await bot.session.close()
        # Clean up lock file
        if os.path.exists("bot.lock"):
            os.remove("bot.lock")


if __name__ == "__main__":
    asyncio.run(main())