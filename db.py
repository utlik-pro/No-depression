import sqlite3
from datetime import datetime
import aiosqlite
from utils import logger


class SQLiteService:
    def __init__(self, db_path="user_state.db"):
        self.db_path = db_path
        self._create_tables()

    def _create_tables(self):
        """Create necessary tables if they don't exist"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                first_name TEXT,
                last_name TEXT,
                username TEXT,
                url TEXT,
                current_question INTEGER DEFAULT 0,
                score INTEGER DEFAULT 0,
                created_at TEXT,
                updated_at TEXT
            )
            ''')

            conn.commit()
            conn.close()
            logger.info("SQLite tables created successfully")
        except Exception as e:
            logger.error(f"Error creating SQLite tables: {e}")

    async def save_user(self, user_data):
        """
        Save user information to the database
        """
        try:
            async with aiosqlite.connect(self.db_path) as db:
                # Check if user already exists
                async with db.execute("SELECT id FROM users WHERE id = ?", (user_data["id"],)) as cursor:
                    existing_user = await cursor.fetchone()

                current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

                if existing_user:
                    # Update existing user
                    await db.execute(
                        """UPDATE users SET 
                           first_name = ?, last_name = ?, username = ?, url = ?, updated_at = ?
                           WHERE id = ?""",
                        (user_data["first_name"], user_data["last_name"], user_data["username"],
                         user_data["url"], current_time, user_data["id"])
                    )
                else:
                    # Insert new user
                    await db.execute(
                        """INSERT INTO users 
                           (id, first_name, last_name, username, url, current_question, score, created_at, updated_at)
                           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                        (user_data["id"], user_data["first_name"], user_data["last_name"],
                         user_data["username"], user_data["url"], 0, 0, current_time, current_time)
                    )

                await db.commit()
                logger.info(f"User {user_data['id']} saved to SQLite")
                return True

        except Exception as e:
            logger.error(f"Error saving user to SQLite: {e}")
            return False

    async def save_test_progress(self, progress_data):
        """
        Save test progress directly to the users table
        """
        try:
            async with aiosqlite.connect(self.db_path) as db:
                current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

                # Update user record with test progress
                await db.execute(
                    """UPDATE users SET 
                       current_question = ?, score = ?, updated_at = ?
                       WHERE id = ?""",
                    (progress_data["current_question"], progress_data["score"],
                     current_time, progress_data["user_id"])
                )

                await db.commit()
                logger.info(f"Test progress for user {progress_data['user_id']} saved to SQLite")
                return True

        except Exception as e:
            logger.error(f"Error saving test progress to SQLite: {e}")
            return False

    async def get_test_progress(self, user_id):
        """
        Get test progress from the users table
        """
        try:
            async with aiosqlite.connect(self.db_path) as db:
                async with db.execute(
                        "SELECT current_question, score FROM users WHERE id = ?",
                        (user_id,)
                ) as cursor:
                    progress_row = await cursor.fetchone()

                if progress_row:
                    return {
                        "user_id": user_id,
                        "current_question": progress_row[0],
                        "score": progress_row[1]
                    }
                return None

        except Exception as e:
            logger.error(f"Error getting test progress from SQLite: {e}")
            return None

    async def reset_test_progress(self, user_id):
        """
        Reset test progress in the users table
        """
        try:
            async with aiosqlite.connect(self.db_path) as db:
                current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

                await db.execute(
                    """UPDATE users SET 
                       current_question = ?, score = ?, updated_at = ?
                       WHERE id = ?""",
                    (0, 0, current_time, user_id)
                )

                await db.commit()
                logger.info(f"Test progress for user {user_id} reset in SQLite")
                return True

        except Exception as e:
            logger.error(f"Error resetting test progress in SQLite: {e}")
            return False

    async def get_all_users(self):
        """
        Get all user IDs from the database
        """
        try:
            async with aiosqlite.connect(self.db_path) as db:
                async with db.execute("SELECT id FROM users") as cursor:
                    rows = await cursor.fetchall()

                return [row[0] for row in rows]

        except Exception as e:
            logger.error(f"Error getting users from SQLite: {e}")
            return []
