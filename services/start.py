from random import shuffle
from utils import logger
from config import TEST_TYPES
import json


class StartService:
    def __init__(self, sheets_service, sqlite_service):
        self.sheets_service = sheets_service
        self.sqlite_service = sqlite_service

    async def init_demographic_questions(self, user_id):
        """
        Initialize the demographic questions phase for a user
        """
        # Set the current phase to demographic
        await self.sqlite_service.init_demographic_questions(user_id)

        # Log the initialization
        logger.info(f"Demographic questions initialized for user {user_id}")

    async def update_demographic_question(self, user_id, question_num):
        """
        Update the current demographic question number
        """
        await self.sqlite_service.update_demographic_question(user_id, question_num)

    async def init_mixed_test(self, user_info):
        """
        Initialize a mixed test with questions from both depression and anxiety tests
        """
        # Create a mixed order of questions
        question_order = []

        # Add depression questions
        depression_questions = TEST_TYPES["depression"]["total_questions"]
        for i in range(depression_questions):
            question_order.append({
                "test_type": "depression",
                "question_idx": i
            })

        # Add anxiety questions
        anxiety_questions = TEST_TYPES["anxiety"]["total_questions"]
        for i in range(anxiety_questions):
            question_order.append({
                "test_type": "anxiety",
                "question_idx": i
            })

        # Shuffle the questions
        shuffle(question_order)

        # Save the order in the user's progress
        user_id = user_info["id"]

        # Convert question_order to JSON for storage
        question_order_json = json.dumps(question_order)

        # Update user progress in database
        await self.sqlite_service.save_mixed_test_progress({
            "user_id": user_id,
            "question_order_json": question_order_json,
            "current_question": 1
        })

        # Reset test scores
        await self.sqlite_service.save_test_result(user_id, "depression", 0)
        await self.sqlite_service.save_test_result(user_id, "anxiety", 0)

        logger.info(f"Mixed test initialized for user {user_id} with {len(question_order)} questions")

    async def get_test_progress(self, user_id):
        """
        Get the current test progress including question order
        """
        progress = await self.sqlite_service.get_test_progress(user_id)

        if progress and progress.get('question_order_json'):
            # Convert JSON string back to list of dictionaries
            progress['question_order'] = json.loads(progress['question_order_json'])

        return progress

    async def update_question_progress(self, user_id, next_question):
        """
        Update the current question index
        """
        await self.sqlite_service.update_question_progress(user_id, next_question)

    async def save_test_result(self, user_id, test_type, score):
        """
        Save test result to the database
        """
        return await self.sqlite_service.save_test_result(user_id, test_type, score)

    async def reset_test_progress(self, user_id, keep_results=False):
        """
        Reset test progress in the database
        """
        return await self.sqlite_service.reset_test_progress(user_id, keep_results)

    def get_combined_recommendation(self, depression_score, anxiety_score):
        """
        Generate recommendation based on combined depression and anxiety scores
        with empathetic language, emojis and promotion code
        """
        # Determine depression severity
        depression_severity = None
        if depression_score >= 8 and depression_score <= 10:
            depression_severity = "субклинический уровень депрессии"
        elif depression_score > 10:
            depression_severity = "клинически выраженный уровень депрессии"

        # Determine anxiety severity
        anxiety_severity = None
        if anxiety_score >= 10 and anxiety_score <= 18:
            anxiety_severity = "умеренный уровень тревожности"
        elif anxiety_score >= 19 and anxiety_score <= 29:
            anxiety_severity = "средний уровень тревожности"
        elif anxiety_score >= 30:
            anxiety_severity = "высокий уровень тревожности"

        # Build empathetic recommendation message
        message = "Результаты вашего теста❗️\n"

        # Add specific results based on what was detected
        if depression_severity and anxiety_severity:
            # Both depression and anxiety detected
            message += f"⚠️ Мы видим у вас {depression_severity} и {anxiety_severity}. \n"
            message += "💪 Важно знать, что вы не одиноки в своих переживаниях, и есть способы улучшить ваше состояние.\n"
        elif depression_severity:
            # Only depression detected
            message += f"⚠️ Мы видим у вас {depression_severity}. \n"
            message += "💪 Помните, что это состояние поддается лечению, и многие люди успешно справляются с подобными трудностями.\n"
        elif anxiety_severity:
            # Only anxiety detected
            message += f"⚠️ Мы видим у вас {anxiety_severity}. \n"
            message += "💪 Беспокойство - это нормальная реакция на стресс, но когда оно становится постоянным, важно обратить на это внимание.\n"
        else:
            # Nothing significant detected
            message += "Ваши результаты в пределах нормы. \n"
            message += "👍 Это хороший знак, но помните, что забота о психическом здоровье важна всегда.\n"

        # Add recommendations based on scores
        if depression_score > 10 or anxiety_score >= 19:
            message += "🩺 Мы искренне рекомендуем вам обратиться к специалисту. Профессиональная помощь может значительно улучшить качество вашей жизни и эмоциональное состояние.\n"
            message += "📞 Запишитесь на консультацию к нашим психотерапевтам уже сегодня! \n"
            message += "Используйте промокод НЕТДЕПРЕССИИ для скидки \n10% \nна первый визит в медицинский центр META CLINIC (https://metaclinic.by).\n"
        elif depression_score >= 8 or anxiety_score >= 10:
            message += "🔍 Рекомендуем вам обратить внимание на своё эмоциональное состояние и изучить методы самопомощи. Также консультация специалиста может быть полезной.\n"
            message += "Если вы решите обратиться к психотерапевту, используйте промокод НЕТДЕПРЕССИИ для скидки \n10% \nна первую консультацию в медицинский центр META CLINIC (https://metaclinic.by).\n"
        else:
            message += "🔎 Продолжайте следить за своим самочувствием.\n"
            message += " Профилактические консультации с психотерапевтом также могут быть полезны для поддержания эмоционального благополучия.\n"
            message += "Если вы заинтересованы в профилактической консультации, используйте промокод НЕТДЕПРЕССИИ для скидки \n10% \nна первый визит в медицинский центр META CLINIC (https://metaclinic.by).\n"

        message += "Забота о себе — это проявление силы, а не слабости. Спасибо за прохождение теста!"

        return message
