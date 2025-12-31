from datetime import datetime

from aiogram import Router, types
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from config import (ADMIN, TEST_TYPES, ANXIETY_SCORES, CONSENT_MESSAGE,
                    CONSENT_OPTIONS, CONSENT_ACCEPTED_MESSAGE, CONSENT_DECLINED_MESSAGE)
from utils import logger


class TelegramRouter:
    def __init__(self, bot, start_service, news_service, sheets_service, sqlite_service, analytics_service=None):
        """
        Initialize the TelegramRouter
        """
        self.bot = bot
        self.start_service = start_service
        self.news_service = news_service
        self.sheets_service = sheets_service
        self.sqlite_service = sqlite_service
        self.analytics_service = analytics_service
        self.router = Router()
        self.setup_routes()

    def setup_routes(self):
        """Set up all the telegram bot command and message handlers"""

        @self.router.message(Command("start"))
        async def start(message: types.Message):
            """
            Handler for /start command
            Starts with consent, then demographic questions, then proceeds to mixed depression and anxiety test
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

            # Save user info
            await self.sqlite_service.save_user(user_info)

            # Track session start
            if self.analytics_service:
                await self.analytics_service.track_session_start(user_info["id"])

            # Send consent message
            keyboard = self.create_answer_keyboard(CONSENT_OPTIONS)
            await message.answer(CONSENT_MESSAGE, reply_markup=keyboard)

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
            Handle button text responses for demographic questions and mixed test answers
            """
            user_id = str(message.from_user.id)

            # Get current test progress from database
            progress = await self.start_service.get_test_progress(user_id)

            if not progress:
                await message.answer(
                    "Чтобы начать тест, пожалуйста, отправьте команду /start"
                )
                return

            # Check if we're in consent phase
            if progress.get('current_phase') == 'consent':
                await self.process_consent_response(message)
                return

            # Check if we're in demographic questions phase
            if progress.get('current_phase') == 'demographic':
                await self.process_demographic_response(message)
                return

            # Get current question index in the mixed test
            if not progress.get('question_order'):
                await message.answer(
                    "Чтобы начать тест, пожалуйста, отправьте команду /start"
                )
                return

            # Get current question index in the mixed test (THIS SECTION WAS INCORRECTLY INDENTED)
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

            # Get user gender for proper formatting
            user_gender = progress.get('gender')  # Add this line to get user gender

            # Find the selected option index
            try:
                # Format the options based on gender before comparison
                if test_type == "depression" and progress.get('gender'):
                    formatted_options = [self.format_gender_specific_text(option, progress.get('gender')) for option in
                                         options]
                    option_idx = formatted_options.index(message.text)
                else:
                    option_idx = options.index(message.text)

                # Get the score for this option
                if test_type == "anxiety":
                    score = test_info['scores'][0][option_idx]
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
                                               len(progress['question_order']), user_gender)
                return

            # Save user's answer to sheets
            question_text = test_info['questions'][question_idx]
            user_response = f"Ответ на вопрос ({test_type}): {message.text} (Балл: {score})"
            await self.sheets_service.save_message_history(user_id, "user", user_response, score)

            # Track test answer
            if self.analytics_service:
                await self.analytics_service.track_test_answer(
                    user_id, current_idx, test_type, score, message.text
                )

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

                # Track test completion
                if self.analytics_service:
                    await self.analytics_service.track_test_complete(
                        user_id, final_depression, final_anxiety
                    )

                # Mark test as completed in Supabase
                if hasattr(self.sqlite_service, 'mark_test_completed'):
                    await self.sqlite_service.mark_test_completed(user_id)

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
                    len(progress['question_order']),
                    user_gender
                )

    async def process_consent_response(self, message):
        """
        Process responses to consent question
        """
        user_id = str(message.from_user.id)

        # Check if user selected consent option
        if message.text == CONSENT_OPTIONS[0]:  # ✅ Согласен на обработку данных
            # Save consent
            await self.sqlite_service.save_consent(user_id)

            # Track consent given
            if self.analytics_service:
                await self.analytics_service.track_consent(user_id, consented=True)

            # Send acceptance message
            await message.answer(CONSENT_ACCEPTED_MESSAGE)

            # Start with demographic questions
            demographic_question = TEST_TYPES["demographic"]["questions"][0]
            demographic_options = TEST_TYPES["demographic"]["options"][0]

            # Create keyboard with options
            keyboard = self.create_answer_keyboard(demographic_options)

            # Send first demographic question
            await message.answer(demographic_question, reply_markup=keyboard)

            # Initialize demographic questions sequence
            await self.start_service.init_demographic_questions(user_id)

        elif message.text == CONSENT_OPTIONS[1]:  # ❌ Не согласен
            # Track consent declined
            if self.analytics_service:
                await self.analytics_service.track_consent(user_id, consented=False)

            # Send decline message
            await message.answer(CONSENT_DECLINED_MESSAGE)

            # Reset user progress
            await self.start_service.reset_test_progress(user_id)
        else:
            # Invalid response, resend consent message
            keyboard = self.create_answer_keyboard(CONSENT_OPTIONS)
            await message.answer(
                "Пожалуйста, используйте предложенные кнопки для ответа.",
                reply_markup=keyboard
            )
            await message.answer(CONSENT_MESSAGE, reply_markup=keyboard)

    async def process_demographic_response(self, message):
        """
        Process responses to demographic questions
        """
        user_id = str(message.from_user.id)
        progress = await self.start_service.get_test_progress(user_id)

        current_question = progress.get('demographic_question', 0)

        # Получить текущие варианты ответов для этого демографического вопроса
        demographic_options = TEST_TYPES["demographic"]["options"][current_question]

        # Проверить, что ответ пользователя соответствует одному из вариантов
        if message.text not in demographic_options:
            # Если ответ не соответствует ни одному из вариантов, отправить сообщение с напоминанием
            keyboard = self.create_answer_keyboard(demographic_options)
            current_question_text = TEST_TYPES["demographic"]["questions"][current_question]
            await message.answer(
                "Пожалуйста, используйте предложенные кнопки для ответа.",
                reply_markup=keyboard
            )
            # Отправить текущий вопрос снова
            await message.answer(current_question_text, reply_markup=keyboard)
            return

        # Track demographic answer
        if self.analytics_service:
            await self.analytics_service.track_demographic_answer(user_id, current_question, message.text)

        # Сохранить ответ на текущий демографический вопрос
        if current_question == 0:  # Gender
            await self.sqlite_service.save_demographic_data(user_id, message.text, None, None)

            # Send gender-specific video
            await self.send_gender_video(message.chat.id, message.text)

            # Перейти к следующему демографическому вопросу (возраст)
            next_question = current_question + 1
            await self.start_service.update_demographic_question(user_id, next_question)

            # Отправить вопрос о возрасте
            age_question = TEST_TYPES["demographic"]["questions"][next_question]
            age_options = TEST_TYPES["demographic"]["options"][next_question]
            keyboard = self.create_answer_keyboard(age_options)
            await message.answer(age_question, reply_markup=keyboard)

        elif current_question == 1:  # Age
            # Get previously saved gender
            gender = await self.sqlite_service.get_user_gender(user_id)
            await self.sqlite_service.save_demographic_data(user_id, gender, message.text, None)

            # Move to next demographic question (location)
            next_question = current_question + 1
            await self.start_service.update_demographic_question(user_id, next_question)

            # Send location question
            location_question = TEST_TYPES["demographic"]["questions"][next_question]
            location_options = TEST_TYPES["demographic"]["options"][next_question]
            keyboard = self.create_answer_keyboard(location_options)
            await message.answer(location_question, reply_markup=keyboard)

        elif current_question == 2:  # Location
            # Get previously saved gender and age
            gender = await self.sqlite_service.get_user_gender(user_id)
            progress = await self.start_service.get_test_progress(user_id)
            age_group = progress.get('age_group')

            await self.sqlite_service.save_demographic_data(user_id, gender, age_group, message.text)

            # Track demographic phase complete
            if self.analytics_service:
                await self.analytics_service.track_demographic_complete(user_id)

            # Proceed to the mixed test
            # Get demographic info for user
            user_info = {
                "id": user_id,
                "gender": gender
            }

            # Start the mixed test
            await message.answer(
                "Спасибо за предоставленную информацию! Теперь перейдем к тесту на оценку "
                "депрессии и тревоги. Пожалуйста, отвечайте честно на вопросы, используя "
                "предложенные кнопки."
            )

            # Initialize mixed test with the collected information
            await self.start_service.init_mixed_test(user_info)

            # Get the first mixed question
            progress = await self.start_service.get_test_progress(user_id)
            first_question_info = progress['question_order'][0]

            # Send the first mixed test question
            await self.send_mixed_question(
                message.chat.id,
                first_question_info,
                1,
                len(progress['question_order']),
                gender
            )

    async def send_mixed_question(self, chat_id, question_info, current_num, total_questions, user_gender):
        """
        Send a mixed test question with appropriate formatting based on gender
        """
        test_type = question_info['test_type']
        question_idx = question_info['question_idx']

        test_info = TEST_TYPES[test_type]

        # Format question based on gender if needed
        if test_type == "depression":
            question = self.format_depression_question(test_info['questions'][question_idx], user_gender)
            options = self.format_depression_options(test_info['options'][question_idx], user_gender)
        elif test_type == "anxiety":
            question = test_info['questions'][question_idx]
            options = test_info['options'][question_idx]

            # Если в вопросах о тревоге также есть гендерные маркеры
            # question = self.format_gender_specific_text(question, user_gender)
            # options = self.format_anxiety_options(options, user_gender)
        else:
            question = test_info['questions'][question_idx]
            options = test_info['options'][question_idx]

        # Create keyboard with options
        keyboard = self.create_answer_keyboard(options)

        # Add progress indicator
        progress_text = f"Вопрос {current_num} из {total_questions}"

        # Send the question
        await self.bot.send_message(
            chat_id,
            f"{question}\n\n{progress_text}",
            reply_markup=keyboard
        )

    def create_answer_keyboard(self, options):
        """
        Create a keyboard with answer options
        """
        # Create buttons list where each option is in its own row
        buttons = []
        for option in options:
            buttons.append([KeyboardButton(text=option)])

        # Create keyboard with the required keyboard parameter
        keyboard = ReplyKeyboardMarkup(
            keyboard=buttons,
            resize_keyboard=True,
            one_time_keyboard=True
        )

        return keyboard

    def format_gender_specific_text(self, text, gender):
        """
        Форматирует текст в зависимости от пола пользователя.
        :param text: Строка с маркерами {{gender_suffix}} и другими гендерно-зависимыми шаблонами
        :param gender: 'Мужчина' или 'Женщина'
        :return: Отформатированный текст
        """
        if gender == "Женщина":
            # Словарь с заменами для женского рода
            replacements = {
                "стал{{gender_suffix}}": "стала",
                "перестал{{gender_suffix}}": "перестала",
                "способен{{gender_suffix}}": "способна",
                "Неспособен{{gender_suffix}}": "Неспособна",
            }
        else:  # По умолчанию - мужской род
            # Словарь с заменами для мужского рода
            replacements = {
                "{{gender_suffix}}": "",  # способен -> способен
                "стал{{gender_suffix}}": "стал",
                "перестал{{gender_suffix}}": "перестал",
                "способен{{gender_suffix}}": "способен",
                "Неспособен{{gender_suffix}}": "Неспособен",
            }

        # Применяем все замены
        for pattern, replacement in replacements.items():
            text = text.replace(pattern, replacement)

        return text

    def format_depression_question(self, question_text, gender):
        """
        Format depression question text based on user gender
        """
        return self.format_gender_specific_text(question_text, gender)

    def format_depression_options(self, options, gender):
        """
        Format depression options based on user gender
        """
        return [self.format_gender_specific_text(option, gender) for option in options]

    def format_anxiety_options(self, options, gender):
        """
        Format anxiety options based on user gender
        """
        return [self.format_gender_specific_text(option, gender) for option in options]

    def clean_option_text(self, option_text):
        """
        Clean option text from formatting placeholders for comparison
        """
        return option_text.replace("{{gender_suffix}}", "").replace("{{verb_gender}}", "").strip()

    async def send_gender_video(self, chat_id, gender):
        """
        Send gender-specific video after user selects their gender
        TODO: Replace placeholder video paths with actual video file IDs or paths
        """
        try:
            if gender == "Женщина":
                # TODO: Replace with actual video for women
                # await self.bot.send_video(chat_id, video="FEMALE_VIDEO_FILE_ID_HERE")
                # Placeholder: send text message instead
                await self.bot.send_message(chat_id, "📹 [Видео для женщин будет здесь]")
            elif gender == "Мужчина":
                # TODO: Replace with actual video for men
                # await self.bot.send_video(chat_id, video="MALE_VIDEO_FILE_ID_HERE")
                # Placeholder: send text message instead
                await self.bot.send_message(chat_id, "📹 [Видео для мужчин будет здесь]")
        except Exception as e:
            logger.error(f"Error sending gender video: {e}")
