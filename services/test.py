from datetime import datetime

from aiogram.fsm.state import State, StatesGroup
from config import openai_client
from google_sheets import save_user_to_sheets
from utils import logger


class ChatStates(StatesGroup):
    QUESTION_1 = State()
    QUESTION_2 = State()
    QUESTION_3 = State()
    QUESTION_4 = State()
    QUESTION_5 = State()
    QUESTION_6 = State()
    QUESTION_7 = State()
    QUESTION_8 = State()
    QUESTION_9 = State()
    FREE_CHAT = State()


user_data = {}

questions = [
    "У Вас снижен интерес или удовольствие от выполнения ежедневных дел?",
    "У Вас было плохое настроение, Вы были подавлены или испытывали чувство безысходности?",
    "Вам было трудно заснуть или у вас прерывистый сон, или Вы слишком много спали?",
    "Вы были утомлены или у Вас было мало сил?",
    "У вас плохой аппетит или Вы переедали?",
    "Вы плохо о себе думали: считали себя неудачником (неудачницей) или были разочарованы, или считали, что подвели семью?",
    "Вам было трудно сосредоточиться на каждодневных делах таких как, чтение газет или просмотр передач?",
    "Вы двигались или говорили так медленно, что другие это отмечали, или наоборот, Вы были настолько суетливы или беспокойны, что двигались гораздо больше обычного?",
    "Вас посещали мысли о том, что Вам лучше было бы умереть, или о том, чтобы причинить себе какой-либо вред?"
]


# Free communication
async def analyze_and_respond(message_text, question_number=None):
    if question_number is None:
        system_prompt = """Ты - эмпатичный психолог-консультант. 
            Ответь на сообщение пользователя с эмпатией и поддержкой. 
            Не давай конкретных рекомендаций по лечению, но можешь обсуждать общие практики поддержания ментального здоровья.
            Если человек хочет начать тест на депресию - попроси его написать /start"""

        try:
            response = openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": message_text}
                ],
                temperature=0.7
            )
            return 0, response.choices[0].message.content
        except Exception as e:
            logger.error(f"Error in free chat: {e}")
            return 0, "Извините, произошла ошибка. Давайте продолжим наш разговор."

    current_question = questions[question_number]
    next_question = questions[question_number + 1] if question_number < 1 else None

    system_prompt = """Ты - эмпатичный психолог-консультант, проводящий оценку депрессии.
    Сначала определи, является ли сообщение пользователя ответом на вопрос или это уточняющий вопрос.
    Формат вывода обязательно только так: "ЧИСЛО|ТЕКСТ". На первом месте обязательно цифра
    Не используй жирный шрифт! Особенно выделение ** **   
    Словарь: "дн" = "да", "нкт" = "нет" и похожие, где 1 буква неправильная...
    в ** находится действия, которы ты должен заменить своими словами, не пиши их в ответе

    Если пользователь не дал ответ, задал уточняющий вопрос, просто решил пообщаться:
    - Ответь пользователю
    - Но мягко попроси дать ответ на изначальный вопрос
    - Не предлагай следующий вопрос
    - Вернив формате:  -1|*Сам ответ на вопрос*

    Проанализируй ответ пользователя и оцени частоту симптома по шкале:
    0 - Никогда/редко/нет
    1 - Иногда
    2 - Часто/да
    3 - Постоянно/всегда/да, сильно/сильно/очень

    Формат ответа СТРОГО сначала ОДНА ЦИФРА, после |, затем следующий вопрос:
    0-3|*Следующий вопрос*

    Пример: 2|Вы были...

    Если пользователь ответил на текущий вопрос - задай следующий вопрос. Вопросы перефразируй под конкретную ситуацию, делать их менее грубыми и строгими, можешь дополнять или примеры приводить"""

    try:
        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"""Текущий вопрос: {current_question}. Следующий вопрос: {next_question}.
                Ответ пользователя: {message_text}"""}
            ],
            temperature=0.7
        )

        full_response = response.choices[0].message.content
        score_str, response_text = full_response.split('|', 1)
        return int(score_str), response_text.strip()

    except Exception as e:
        print(f"Error in analyze_and_respond: {e}")
        return 0, "Извините, произошла ошибка. Давайте продолжим наш разговор."


async def get_final_recommendation(total_score):
    """Получает финальную рекомендацию от GPT"""
    result = get_result(total_score)

    try:
        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": """Ты - эмпатичный психолог-консультант. 
                Дай ответ на результат теста, но ничего не рекомендуй. В конце ответа дай промокод АА123, который даёт скидку 50% на посещение врача.

                Делай по примеру, если есть признаки депрессии, но лучше немного его перефразируй:
                [Я вижу, что ваш результат теста указывает на наличие признаков тяжелой депрессии. Это может быть очень непростой период, и важно понимать, что вы не одни. 
                Признавать свои чувства и искать поддержку – это уже значимый шаг. Вы нуждаетесь в поддержке, это абсолютно нормально.
                Обращение к специалисту станет важным этапом на пути к улучшению самочувствия.Помните, что заботиться о себе – это важно.
                Не бойтесь обратиться к врачу, у вас есть возможность воспользоваться промокодом АА123, который даст вам скидку 50% на посещение психотерапевта. 
                Заботьтесь о себе и не стесняйтесь обращаться за помощью, она ближе чем вы думаете.]
                """},

                {"role": "user", "content": f"Результат теста: {total_score} баллов. {result}"}
            ],
            temperature=0.7
        )

        return response.choices[0].message.content
    except Exception as e:
        print(f"Error in analyze_and_respond: {e}")
        return 0, "Извините, произошла ошибка при формировании рекомендации."


def get_result(score):
    if score <= 4:
        return "У вас минимальные признаки депрессии или их отсутствие."
    elif score <= 9:
        return "Я вижу, что ваш результат теста указывает на наличие признаков лёгкой депрессии."
    elif score <= 14:
        return "Я вижу, что ваш результат теста указывает на наличие признаков умеренной депрессии."
    else:
        return "Я вижу, что ваш результат теста указывает на наличие признаков тяжелой депрессии."


async def test(message, state):
    current_datetime = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    user_data = {
        "id": str(message.from_user.id),
        "first_name": message.from_user.first_name or "",
        "last_name": message.from_user.last_name or "",
        "username": message.from_user.username or "",
        "url": f"https://t.me/{message.from_user.username}" if message.from_user.username else "",
        "datetime": current_datetime,
    }

    # Save user data to GoogleSheets
    await save_user_to_sheets(user_data)

    user_id = message.from_user.id
    user_data[user_id] = {'score': 0, 'question_number': None}

    intro_message = (
        "Здравствуйте! Я ваш помощник по ментальному здоровью. "
        "Давайте поговорим о том, как вы себя чувствуете.\n\n"
        "Я задам вам несколько вопросов. Пожалуйста, отвечайте искренне, "
        "своими словами, как чувствуете. \nВ любой момент вы можете "
        "поделиться своими мыслями или задать мне вопрос."
    )

    await message.answer(intro_message)
    await state.set_state(ChatStates.QUESTION_1)
    await message.answer(questions[0])
