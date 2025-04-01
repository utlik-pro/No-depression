from datetime import datetime
from aiogram import Router, types
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from config import ADMIN, QUESTIONS
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
            Initializes a new test session for the user
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

            # Reset user test progress if user restarted the test
            await self.start_service.update_test_progress(user_info["id"], 0, 1)

            # Send introductory message
            intro_message = (
                "Здравствуйте! Я ваш помощник по ментальному здоровью. "
                "Давайте проверим ваше текущее состояние с помощью теста.\n\n"
                "Я задам вам несколько вопросов. Пожалуйста, отвечайте на них, "
                "используя предложенные кнопки."
            )

            await message.answer(intro_message)

            # Initialize the test (this already sets everything up correctly)
            await self.start_service.init_test(user_info)

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
            Handle button text responses for test answers
            Processes user responses to test questions and calculates scores
            """
            user_id = str(message.from_user.id)

            # Get current test progress from database
            progress = await self.start_service.get_test_progress(user_id)

            if not progress:
                await message.answer(
                    "Чтобы начать тест, пожалуйста, отправьте команду /start"
                )
                return

            # Check if test is complete
            if progress['current_question'] == 0:
                await message.answer(
                    "Чтобы начать тест, пожалуйста, отправьте команду /start"
                )
                return

            # Map answer text to score values
            answer_mapping = {
                "Ни разу": 0,
                "Несколько дней": 1,
                "Больше половины времени": 2,
                "Почти каждый день": 3
            }

            score = answer_mapping.get(message.text)

            if score is None:
                # If not a valid button response, remind to use buttons
                await message.answer(
                    "Пожалуйста, используйте кнопки для ответа на вопрос.",
                    reply_markup=self.answer_question_menu()
                )

                # Resend the current question
                await self.send_question(message.chat.id, progress['current_question'])
                return

            # Get current question number from database
            question_number = progress['current_question']

            logger.info(f"Processing answer for question {question_number}, score: {score}")

            # Save user's answer to both SQLite and Google Sheets
            user_response = f"Ответ на вопрос {question_number}: {self.get_answer_text(score)}"
            await self.sheets_service.save_message_history(user_id, "user", user_response, score)

            # Update test progress in database
            updated_score = progress['score'] + score
            next_question = question_number + 1

            # Check if this was the last question
            if next_question >= 9:  # Assuming 9 questions total
                final_score = updated_score
                recommendation = self.get_recommendation(final_score)

                await message.answer(recommendation)

                # Save final recommendation to both storages
                await self.sheets_service.save_message_history(user_id, "bot", recommendation, final_score)

                # Clear test progress as it's complete
                await self.start_service.reset_test_progress(user_id)
            else:
                # Update score and move to next question
                await self.start_service.update_test_progress(user_id, updated_score, next_question)

                # Send next question
                await self.send_question(message.chat.id, next_question)

    async def send_next_question(self, chat_id):
        """
        Send the next question based on user's progress in DB
        """
        user_id = str(chat_id)
        progress = await self.start_service.get_test_progress(user_id)

        if not progress:
            logger.error(f"No test progress found for user {user_id}")
            return

        question_number = progress['current_question']
        await self.send_question(chat_id, question_number)

    async def send_question(self, chat_id, question_number):
        """
        Send a question with answer buttons
        """
        if question_number >= len(QUESTIONS):
            logger.error(f"Invalid question number: {question_number}")
            return

        question_text = QUESTIONS[question_number]
        keyboard = self.answer_question_menu()

        # Display question_number as 1-indexed while keeping the logic 0-indexed
        display_number = question_number + 1 if question_number == 0 else question_number

        await self.bot.send_message(
            chat_id=chat_id,
            text=f"Вопрос {display_number}/9:\n\n{question_text}",
            reply_markup=keyboard
        )

        # Save bot message to Google Sheets with the displayed question number
        bot_message = f"Вопрос {display_number}: {question_text}"
        await self.sheets_service.save_message_history(str(chat_id), "bot", bot_message)

    @staticmethod
    def answer_question_menu():
        """
        Create reply keyboard with answer options
        """
        return ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="Ни разу")],
                [KeyboardButton(text="Несколько дней")],
                [KeyboardButton(text="Больше половины времени")],
                [KeyboardButton(text="Почти каждый день")]
            ],
            resize_keyboard=True,
            one_time_keyboard=True
        )

    @staticmethod
    def get_answer_text(score):
        """
        Get score from buttons
        """
        answers = {
            0: "Ни разу",
            1: "Несколько дней",
            2: "Больше половины времени",
            3: "Почти каждый день"
        }
        return answers.get(score, "Неизвестный ответ")

    @staticmethod
    def get_recommendation(score):
        """
        Get recommendation based on final score
        """
        if score <= 4:
            result = "У вас минимальные признаки депрессии или их отсутствие."
            answer = """Это хороший знак, и, возможно, вы сейчас находитесь в более устойчивом эмоциональном состоянии. Важно помнить, что поддерживать свое психическое здоровье – это постоянный процесс.
\nЕсли у вас возникнут вопросы или вы почувствуете необходимость в обсуждении своих эмоций, не стесняйтесь обращаться за поддержкой. Забота о себе всегда важна. 
\nЕсли вы решите обратиться к специалисту, у вас есть возможность использовать промокод АА123, который предоставляет скидку 50% на посещение врача. 
\nЗаботьтесь о себе и оставайтесь в гармонии с собой 🤗"""
        elif score <= 9:
            result = "У вас есть признаки лёгкой депрессии."
            answer = """Симптомы указывают на незначительные изменения в эмоциональном состоянии. Это сигнал обратить внимание на своё самочувствие: возможно, стоит пересмотреть режим дня, включить больше физической активности и отдых.
\nЕсли состояние сохраняется, подумайте о беседе со специалистом. 
\nПомните, поддержка важна – используйте промокод АА123 для консультации по сниженной цене."""
        elif score <= 14:
            result = "У вас есть признаки умеренной депрессии."
            answer = """Ваше состояние требует внимания – симптомы умеренной депрессии могут влиять на повседневную жизнь. Рекомендуется уделить время самоанализу, попробовать техники релаксации и, возможно, обратиться за профессиональной помощью.
\nПсихотерапевт поможет разобраться в причинах и подобрать оптимальную стратегию поддержки.
\nИспользуйте промокод АА123 для скидки 50% на визит к специалисту."""
        else:
            result = "У вас есть признаки тяжелой депрессии."
            answer = """Это может быть непростой период, и важно понимать, что Вы не одни. Признавать свои чувства и искать поддержку – это уже значимый шаг. Помните, что заботиться о себе – это важно.
\nНе бойтесь обратиться к врачу, у вас есть возможность воспользоваться промокодом АА123, который даст вам скидку 50% на посещение психотерапевта.
\nЗаботьтесь о себе и не стесняйтесь обращаться за помощью, она ближе чем вы думаете 🤗"""

        return f"""Результат теста: {result} \n\n{answer}"""
