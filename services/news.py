import asyncio
from aiogram import Bot
from utils import logger


class NewsService:
    def __init__(self, bot: Bot, sheets_service):
        """
        Initialize the news service
        """
        self.bot = bot
        self.sheets_service = sheets_service

    async def broadcast_news(self, message_text):
        """
        Initialize the news service
        """
        users = await self.sheets_service.get_all_users_from_sheets()
        success_count = 0
        fail_count = 0

        for user_id in users:
            try:
                await self.bot.send_message(user_id, message_text)
                success_count += 1
                await asyncio.sleep(0.1)
            except Exception as e:
                logger.error(f"Failed to send message to user {user_id}: {e}")
                fail_count += 1

        return success_count, fail_count
