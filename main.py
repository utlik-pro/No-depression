import asyncio
import threading
import uvicorn
from aiogram import Dispatcher, Bot
from config import TOKEN, API_HOST, API_PORT, SUPABASE_URL
from db import SQLiteService
from google_sheets import SheetsService
from handlers import TelegramRouter
from services.news import NewsService
from services.start import StartService
from services.analytics import AnalyticsService
from utils import logger

# Conditionally import Supabase service
if SUPABASE_URL:
    from services.supabase_service import SupabaseService


def run_api_server():
    """Run FastAPI server in a separate thread"""
    from api.app import app
    uvicorn.run(app, host=API_HOST, port=API_PORT, log_level="info")


async def main():
    # Initialize bot and dispatcher
    bot = Bot(token=TOKEN)
    dp = Dispatcher()

    # Initialize services
    sheets_service = SheetsService()
    sqlite_service = SQLiteService(db_path="nodepressionbot.db")

    # Initialize Supabase if configured
    supabase_service = None
    if SUPABASE_URL:
        supabase_service = SupabaseService()
        logger.info("Supabase service initialized")

    # Use Supabase for bot if available, otherwise fallback to SQLite
    db_service = supabase_service if supabase_service else sqlite_service

    start_service = StartService(sheets_service, db_service)
    news_service = NewsService(bot, sheets_service)

    # Initialize analytics service
    analytics_service = AnalyticsService() if SUPABASE_URL else None

    # Initialize router with analytics
    telegram_router = TelegramRouter(
        bot,
        start_service,
        news_service,
        sheets_service,
        db_service,
        analytics_service
    )

    # Register router
    dp.include_router(telegram_router.router)

    # Start FastAPI server in background thread
    api_thread = threading.Thread(target=run_api_server, daemon=True)
    api_thread.start()
    logger.info(f"API server started on http://{API_HOST}:{API_PORT}")

    # Start bot polling
    logger.info("Starting Telegram bot")
    await dp.start_polling(bot, skip_updates=True)


if __name__ == "__main__":
    asyncio.run(main())
