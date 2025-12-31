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
                gender TEXT,
                age_group TEXT,
                location TEXT,
                current_question INTEGER DEFAULT 0,
                question_order_json TEXT,
                depression_score INTEGER DEFAULT -1,
                anxiety_score INTEGER DEFAULT -1,
                demographic_question INTEGER DEFAULT 0,
                current_phase TEXT DEFAULT 'consent',
                consent_given INTEGER DEFAULT 0,
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
                           first_name = ?, last_name = ?, username = ?, url = ?, 
                           current_phase = 'demographic', demographic_question = 0, updated_at = ?
                           WHERE id = ?""",
                        (user_data["first_name"], user_data["last_name"], user_data["username"],
                         user_data["url"], current_time, user_data["id"])
                    )
                else:
                    # Insert new user
                    await db.execute(
                        """INSERT INTO users 
                           (id, first_name, last_name, username, url, current_question,
                           depression_score, anxiety_score, demographic_question, current_phase, created_at, updated_at)
                           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                        (user_data["id"], user_data["first_name"], user_data["last_name"],
                         user_data["username"], user_data["url"], 0, -1, -1, 0, 'demographic', current_time,
                         current_time)
                    )

                await db.commit()
                logger.info(f"User {user_data['id']} saved to SQLite")
                return True

        except Exception as e:
            logger.error(f"Error saving user to SQLite: {e}")
            return False

    async def init_demographic_questions(self, user_id):
        """
        Initialize the demographic questions phase for a user
        """
        try:
            async with aiosqlite.connect(self.db_path) as db:
                current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

                # Set the current phase to demographic and reset demographic question counter
                await db.execute(
                    """UPDATE users SET 
                       current_phase = 'demographic', demographic_question = 0, updated_at = ?
                       WHERE id = ?""",
                    (current_time, user_id)
                )

                await db.commit()
                logger.info(f"Demographic questions initialized for user {user_id}")
                return True

        except Exception as e:
            logger.error(f"Error initializing demographic questions in SQLite: {e}")
            return False

    async def save_demographic_data(self, user_id, gender, age_group, location):
        """
        Save demographic data for a user
        """
        try:
            async with aiosqlite.connect(self.db_path) as db:
                current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

                # Update user record with demographic data
                await db.execute(
                    """UPDATE users SET 
                       gender = ?, age_group = ?, location = ?, updated_at = ?
                       WHERE id = ?""",
                    (gender, age_group, location, current_time, user_id)
                )

                await db.commit()
                logger.info(f"Demographic data for user {user_id} saved to SQLite")
                return True

        except Exception as e:
            logger.error(f"Error saving demographic data to SQLite: {e}")
            return False

    async def update_demographic_question(self, user_id, question_num):
        """
        Update the current demographic question number
        """
        try:
            async with aiosqlite.connect(self.db_path) as db:
                current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

                await db.execute(
                    """UPDATE users SET 
                       demographic_question = ?, updated_at = ?
                       WHERE id = ?""",
                    (question_num, current_time, user_id)
                )

                await db.commit()
                logger.info(f"Demographic question for user {user_id} updated to {question_num}")
                return True

        except Exception as e:
            logger.error(f"Error updating demographic question in SQLite: {e}")
            return False

    async def get_user_gender(self, user_id):
        """
        Get user's gender from the database
        """
        try:
            async with aiosqlite.connect(self.db_path) as db:
                async with db.execute("SELECT gender FROM users WHERE id = ?", (user_id,)) as cursor:
                    gender_row = await cursor.fetchone()

                return gender_row[0] if gender_row else None

        except Exception as e:
            logger.error(f"Error getting user gender from SQLite: {e}")
            return None

    async def save_mixed_test_progress(self, progress_data):
        """
        Save mixed test progress to the users table
        """
        try:
            async with aiosqlite.connect(self.db_path) as db:
                current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

                # Update user record with mixed test progress
                await db.execute(
                    """UPDATE users SET 
                       question_order_json = ?, current_question = ?, current_phase = 'mixed_test', updated_at = ?
                       WHERE id = ?""",
                    (progress_data["question_order_json"], progress_data["current_question"],
                     current_time, progress_data["user_id"])
                )

                await db.commit()
                logger.info(f"Mixed test progress for user {progress_data['user_id']} saved to SQLite")
                return True

        except Exception as e:
            logger.error(f"Error saving mixed test progress to SQLite: {e}")
            return False

    async def update_question_progress(self, user_id, next_question):
        """
        Update the current question index for a user
        """
        try:
            async with aiosqlite.connect(self.db_path) as db:
                current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

                await db.execute(
                    """UPDATE users SET 
                       current_question = ?, updated_at = ?
                       WHERE id = ?""",
                    (next_question, current_time, user_id)
                )

                await db.commit()
                logger.info(f"Question progress for user {user_id} updated to {next_question}")
                return True

        except Exception as e:
            logger.error(f"Error updating question progress in SQLite: {e}")
            return False

    async def save_test_result(self, user_id, test_type, score):
        """
        Save test result to the users table
        """
        try:
            async with aiosqlite.connect(self.db_path) as db:
                current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

                if test_type == "depression":
                    await db.execute(
                        """UPDATE users SET 
                           depression_score = ?, updated_at = ?
                           WHERE id = ?""",
                        (score, current_time, user_id)
                    )
                elif test_type == "anxiety":
                    await db.execute(
                        """UPDATE users SET 
                           anxiety_score = ?, updated_at = ?
                           WHERE id = ?""",
                        (score, current_time, user_id)
                    )

                await db.commit()
                logger.info(f"{test_type.capitalize()} test result for user {user_id} saved to SQLite: {score}")
                return True

        except Exception as e:
            logger.error(f"Error saving test result to SQLite: {e}")
            return False

    async def get_test_progress(self, user_id):
        """
        Get test progress from the users table including question order
        """
        try:
            async with aiosqlite.connect(self.db_path) as db:
                async with db.execute(
                        """SELECT current_question, question_order_json, depression_score, anxiety_score, 
                           gender, current_phase, demographic_question, age_group FROM users WHERE id = ?""",
                        (user_id,)
                ) as cursor:
                    progress_row = await cursor.fetchone()

                if progress_row:
                    return {
                        "user_id": user_id,
                        "current_question": progress_row[0],
                        "question_order_json": progress_row[1],
                        "depression_score": progress_row[2],
                        "anxiety_score": progress_row[3],
                        "gender": progress_row[4],
                        "current_phase": progress_row[5],
                        "demographic_question": progress_row[6],
                        "age_group": progress_row[7]
                    }
                return None

        except Exception as e:
            logger.error(f"Error getting test progress from SQLite: {e}")
            return None

    async def reset_test_progress(self, user_id, keep_results=False):
        """
        Reset test progress in the users table, optionally keeping test results
        """
        try:
            async with aiosqlite.connect(self.db_path) as db:
                current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

                if keep_results:
                    await db.execute(
                        """UPDATE users SET 
                           question_order_json = NULL, current_question = 0, current_phase = 'demographic',
                           demographic_question = 0, updated_at = ?
                           WHERE id = ?""",
                        (current_time, user_id)
                    )
                else:
                    await db.execute(
                        """UPDATE users SET 
                           question_order_json = NULL, current_question = 0, current_phase = 'demographic',
                           demographic_question = 0, depression_score = -1, anxiety_score = -1, updated_at = ?
                           WHERE id = ?""",
                        (current_time, user_id)
                    )

                await db.commit()
                logger.info(f"Test progress for user {user_id} reset in SQLite")
                return True

        except Exception as e:
            logger.error(f"Error resetting test progress in SQLite: {e}")
            return False

    async def save_consent(self, user_id):
        """
        Save user's consent for data processing
        """
        try:
            async with aiosqlite.connect(self.db_path) as db:
                current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

                await db.execute(
                    """UPDATE users SET
                       consent_given = 1, current_phase = 'demographic', updated_at = ?
                       WHERE id = ?""",
                    (current_time, user_id)
                )

                await db.commit()
                logger.info(f"Consent saved for user {user_id}")
                return True

        except Exception as e:
            logger.error(f"Error saving consent in SQLite: {e}")
            return False

    async def get_consent_status(self, user_id):
        """
        Check if user has given consent
        """
        try:
            async with aiosqlite.connect(self.db_path) as db:
                async with db.execute("SELECT consent_given FROM users WHERE id = ?", (user_id,)) as cursor:
                    consent_row = await cursor.fetchone()

                return consent_row[0] == 1 if consent_row else False

        except Exception as e:
            logger.error(f"Error getting consent status from SQLite: {e}")
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
