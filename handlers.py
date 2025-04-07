from datetime import datetime
from aiogram import Router, types
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from config import ADMIN, TEST_TYPES
from utils import logger


class TelegramRouter:
    def __init__(self, bot, start_service, news_service, sheets_service):
        """
        Initialize the TelegramRouter
        """
        self.bot = bot
        self.start_service = start_service
        self.news_service = news_service
        self.sheets_service = sheets_service
        self.router = Router()
        self.setup_routes()

    def setup_routes(self):
        """Set up all the telegram bot command and message handlers"""

        @self.router.message(Command("start"))
        async def start(message: types.Message):
            """
            Handler for /start command
            Initializes a new test session with mixed depression and anxiety questions
            """
            # Collect user information
            user_info = {
                "id": str(message.from_user.id),
                "first_name": message.from_user.first_name or "",
                "last_name": message.from_user.last_name or "",
                "username": message.from_user.username or "",
                "url": f"https://t.me/{message.from_user.username}" if message.from_user.username else "",
                "datetime": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            }

            # Reset user test progress
            await self.start_service.reset_test_progress(user_info["id"])

            # Send introductory message
            intro_message = (
                "Здравствуйте! Я ваш помощник по ментальному здоровью. "
                "Давайте проверим ваше текущее состояние с помощью теста, "
                "который объединяет вопросы о депрессии и тревоге.\n\n"
                "Я задам вам несколько вопросов. Пожалуйста, отвечайте на них, "
                "используя предложенные кнопки."
            )

            await message.answer(intro_message)

            # Initialize the mixed test
            await self.start_service.init_mixed_test(user_info)

            # Send first question with buttons
            await self.send_next_question(message.chat.id)

        @self.router.message(Command("news"))
        async def news(message: types.Message):
            """
            Handler for /news command
            Initiates a broadcast message to all users
            Only accessible by admin
            """
            # Check if message sender is an admin
            if str(message.from_user.id) != ADMIN:
                return

            await message.answer('Starting the mailing...')
            success, fails = await self.news_service.broadcast_news("У нас новая акция!")
            await message.answer(f"Campaign completed!\nSuccessful: {success}\nErrors: {fails}")

        @self.router.message()
        async def process_button_response(message: types.Message):
            """
            Handle button text responses for mixed test answers
            Processes user responses and calculates scores for each test type separately
            """
            user_id = str(message.from_user.id)

            # Get current test progress from database
            progress = await self.start_service.get_test_progress(user_id)

            if not progress or not progress.get('question_order'):
                await message.answer(
                    "Чтобы начать тест, пожалуйста, отправьте команду /start"
                )
                return

            # Get current question index in the mixed test
            current_idx = progress['current_question'] - 1

            # Get the question info from the mixed order
            if current_idx < 0 or current_idx >= len(progress['question_order']):
                await message.answer(
                    "Произошла ошибка с вашим прогрессом. Пожалуйста, отправьте команду /start чтобы начать заново."
                )
                return

            # Get the current question details
            question_info = progress['question_order'][current_idx]
            test_type = question_info['test_type']  # depression or anxiety
            question_idx = question_info['question_idx']  # index within specific test

            test_info = TEST_TYPES[test_type]

            # Get the options for the current question
            options = test_info['options'][question_idx]

            # For anxiety, all questions have the same options
            if isinstance(options[0], str):
                options = options  # It's already just a list of strings
            else:
                options = options[question_idx]  # It's a list of option lists

            # Find the selected option index
            try:
                option_idx = options.index(message.text)
                # Get the score for this option
                if test_type == "anxiety":
                    score = test_info['scores'][0][option_idx]  # All anxiety questions use the same score mapping
                else:
                    score = test_info['scores'][question_idx][option_idx]
            except ValueError:
                # If not a valid button response, remind to use buttons
                keyboard = self.create_answer_keyboard(options)
                await message.answer(
                    "Пожалуйста, используйте кнопки для ответа на вопрос.",
                    reply_markup=keyboard
                )

                # Resend the current question
                await self.send_mixed_question(message.chat.id, question_info, current_idx + 1,
                                               len(progress['question_order']))
                return

            # Save user's answer to sheets
            question_text = test_info['questions'][question_idx]
            user_response = f"Ответ на вопрос ({test_type}): {message.text} (Балл: {score})"
            await self.sheets_service.save_message_history(user_id, "user", user_response, score)

            # Update the appropriate score
            if test_type == "depression":
                depression_score = progress['depression_score']
                depression_score = depression_score + score if depression_score >= 0 else score
                await self.start_service.save_test_result(user_id, "depression", depression_score)
            else:  # anxiety
                anxiety_score = progress['anxiety_score']
                anxiety_score = anxiety_score + score if anxiety_score >= 0 else score
                await self.start_service.save_test_result(user_id, "anxiety", anxiety_score)

            # Move to the next question
            next_question = progress['current_question'] + 1

            # Check if we've completed all questions
            if next_question > len(progress['question_order']):
                # Both tests completed, show results
                # Get the final scores for both tests
                final_progress = await self.start_service.get_test_progress(user_id)
                final_depression = final_progress['depression_score']
                final_anxiety = final_progress['anxiety_score']

                # Generate recommendations based on combined scores
                if final_depression >= 0 and final_anxiety >= 0:
                    # Both tests completed
                    recommendation = self.start_service.get_combined_recommendation(
                        final_depression, final_anxiety
                    )
                else:
                    # Fallback if something went wrong
                    recommendation = "Произошла ошибка при подсчете результатов. Пожалуйста, попробуйте пройти тест еще раз."

                # Send final recommendation
                await message.answer(recommendation)

                # Save the recommendation to sheets
                await self.sheets_service.save_message_history(
                    user_id, "bot", f"Итоговая рекомендация: {recommendation}",
                    {"depression": final_depression, "anxiety": final_anxiety}
                )

                # Reset test progress but keep results
                await self.start_service.reset_test_progress(user_id, keep_results=True)
            else:
                # Update progress to next question
                await self.start_service.update_question_progress(user_id, next_question)

                # Send next question
                next_question_info = progress['question_order'][next_question - 1]
                await self.send_mixed_question(
                    message.chat.id,
                    next_question_info,
                    next_question,
                    len(progress['question_order'])
                )

    async def send_next_question(self, chat_id):
        """
        Send the next question based on user's progress in DB
        """
        user_id = str(chat_id)
        progress = await self.start_service.get_test_progress(user_id)

        if not progress or not progress.get('question_order'):
            logger.error(f"No test progress found for user {user_id}")
            return

        question_number = progress['current_question']
        question_info = progress['question_order'][question_number - 1]

        await self.send_mixed_question(
            chat_id,
            question_info,
            question_number,
            len(progress['question_order'])
        )

    async def send_mixed_question(self, chat_id, question_info, question_number, total_questions):
        """
        Send a question from the mixed test with answer buttons
        """
        test_type = question_info['test_type']
        question_idx = question_info['question_idx']
        test_info = TEST_TYPES[test_type]

        # Get the question text
        question_text = test_info['questions'][question_idx]

        # Get the options
        if test_type == "anxiety":
            options = test_info['options'][0]  # All anxiety questions use the same options
        else:
            options = test_info['options'][question_idx]

        # Create keyboard with answer options
        keyboard = self.create_answer_keyboard(options)

        # Send the question with answer options
        test_name = test_info['name']
        await self.bot.send_message(
            chat_id=chat_id,
            text=f"Вопрос {question_number}/{total_questions}:\n\n{question_text}",
            reply_markup=keyboard
        )

        # Save bot message to Google Sheets
        bot_message = f"{test_name} - Вопрос {question_number}/{total_questions}: {question_text}"
        await self.sheets_service.save_message_history(str(chat_id), "bot", bot_message)

    @staticmethod
    def create_answer_keyboard(options):
        """
        Create reply keyboard with the given answer options
        """
        keyboard = []
        for option in options:
            keyboard.append([KeyboardButton(text=option)])

        return ReplyKeyboardMarkup(
            keyboard=keyboard,
            resize_keyboard=True,
            one_time_keyboard=True
        )
