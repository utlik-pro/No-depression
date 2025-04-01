from utils import logger


class StartService:
    def __init__(self, sheets_service, sqlite_service):
        """
        Initialize the start service
        """
        self.sheets_service = sheets_service
        self.sqlite_service = sqlite_service

    async def init_test(self, user_info):
        """
        Initialize test and save user info
        """
        user_id = user_info["id"]

        # Save user info to both storages
        await self.sqlite_service.save_user(user_info)
        await self.sheets_service.save_user_to_sheets(user_info)

        # Set test progress to question 1
        test_progress = {
            'user_id': user_id,
            'score': 0,
            'current_question': 1
        }
        await self.sqlite_service.save_test_progress(test_progress)

        logger.info(f"Initialized test for user {user_id}")

        # Return initial progress state
        return test_progress

    async def get_test_progress(self, user_id):
        """
        Get current test progress from database
        """
        # Try SQLite first (faster)
        progress = await self.sqlite_service.get_test_progress(user_id)

        # If no progress record exists, return None
        if not progress:
            logger.info(f"No test progress found for user {user_id}")
            return None

        return progress

    async def update_test_progress(self, user_id, score, current_question):
        """
        Update user's test progress in database
        """
        test_progress = {
            'user_id': user_id,
            'score': score,
            'current_question': current_question
        }

        await self.sqlite_service.save_test_progress(test_progress)
        logger.info(f"Updated test progress for user {user_id}: score={score}, question={current_question}")

        return test_progress

    async def reset_test_progress(self, user_id):
        """
        Reset user's test progress
        """
        await self.sqlite_service.reset_test_progress(user_id)
        logger.info(f"Reset test progress for user {user_id}")

        return True
