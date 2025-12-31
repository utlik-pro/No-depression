import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
TOKEN = os.getenv("TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ADMIN = os.getenv("ADMIN")

# Supabase configuration
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# Admin panel configuration
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")
JWT_SECRET = os.getenv("JWT_SECRET", "your-secret-key-change-in-production")
JWT_EXPIRY_HOURS = int(os.getenv("JWT_EXPIRY_HOURS", "24"))
API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("API_PORT", "8000"))

openai_client = OpenAI(api_key=OPENAI_API_KEY)


# Функция для форматирования текста в зависимости от пола
def format_gender_specific_text(text, gender):
    """
    Форматирует текст в зависимости от пола пользователя.
    :param text: Строка с маркерами {{gender_suffix}}
    :param gender: 'Мужчина' или 'Женщина'
    :return: Отформатированный текст
    """
    if gender == "Женщина":
        replacements = {
            "стал{{gender_suffix}}": "стала",
            "перестал{{gender_suffix}}": "перестала",
            "способен{{gender_suffix}}": "способна",
            "Неспособен{{gender_suffix}}": "Неспособна",
        }
    else:  
        replacements = {
            "{{gender_suffix}}": "",
            "стал{{gender_suffix}}": "стал",
            "перестал{{gender_suffix}}": "перестал",
            "способен{{gender_suffix}}": "способен",
            "Неспособен{{gender_suffix}}": "Неспособен",
        }

    for pattern, replacement in replacements.items():
        text = text.replace(pattern, replacement)

    return text


# Consent message and options
CONSENT_MESSAGE = """Здравствуйте! Я Ваш помощник по ментальному здоровью.

Для продолжения работы мне необходимо получить Ваше согласие на обработку персональных данных.

Я буду собирать и обрабатывать следующие данные:
• Ваше имя и username в Telegram
• Демографическую информацию (пол, возраст, регион)
• Ответы на вопросы тестов
• Результаты тестирования

Данные используются исключительно для проведения психологического тестирования и предоставления рекомендаций. Все данные хранятся в защищенном виде и не передаются третьим лицам.

Вы согласны на обработку персональных данных?"""

CONSENT_OPTIONS = ["✅ Согласен на обработку данных", "❌ Не согласен"]

CONSENT_ACCEPTED_MESSAGE = """Спасибо за согласие!

Теперь давайте соберем немного информации о Вас, а затем проверим Ваше текущее состояние с помощью теста, который объединяет вопросы о депрессии и тревоге.

Я задам Вам несколько вопросов. Пожалуйста, отвечайте на них, используя предложенные кнопки."""

CONSENT_DECLINED_MESSAGE = """Спасибо за ответ. К сожалению, без Вашего согласия я не могу проводить тестирование.

Если Вы передумаете, отправьте команду /start снова."""

DEMOGRAPHIC_QUESTIONS = [
    "Выберите Ваш пол.",
    "Сколько Вам лет?",
    "Где Вы проживаете?"
]

DEMOGRAPHIC_OPTIONS = [
    ["Женщина", "Мужчина"],
    ["18-24", "25-34", "35-44", "45-54", "55-64", "65+"],
    ["Минск", "Минская область", "Брестская область", "Витебская область",
     "Гомельская область", "Гродненская область", "Могилевская область"]
]

DEPRESSION_QUESTIONS = [
    "Чувство удовольствия испытываю такое же, как и раньше.",
    "Я способен{{gender_suffix}} увидеть смешное в различных ситуациях и рассмеяться.",
    "Я испытываю бодрость.",
    "Я всё стал{{gender_suffix}} делать медленнее.",
    "Я перестал{{gender_suffix}} следить за своей внешностью.",
    "Мои увлечения и занятия приносят мне чувство удовлетворения.",
    "Я получаю удовольствие от телепрограмм, книг."
]

DEPRESSION_OPTIONS = [
    ["Не испытываю", "Испытываю в малой степени", "Наверное, испытываю", "Очень часто испытываю"],
    ["Неспособен{{gender_suffix}}", "Иногда", "Наверное, это так", "Да, это так"],
    ["Не испытываю", "Очень редко", "Периодически испытываю", "Большинство времени испытываю бодрость"],
    ["Почти постоянно", "Часто", "Иногда", "Не стал{{gender_suffix}}"],
    ["Определенно, это так", "Я очень мало внимания уделяю своей внешности",
     "Я стал{{gender_suffix}} уделять меньше внимания внешности", "Я слежу за своей внешностью"],
    ["Я так не считаю", "Значительно реже, чем раньше", "Не в той степени, как раньше",
     "Ничего не изменилось, всё по-прежнему"],
    ["Очень редко", "Редко", "Иногда", "Часто"]
]

DEPRESSION_SCORES = [
    [3, 2, 1, 0],
    [3, 2, 1, 0],
    [3, 2, 1, 0],
    [3, 2, 1, 0],
    [3, 2, 1, 0],
    [3, 2, 1, 0],
    [3, 2, 1, 0]
]

ANXIETY_QUESTIONS = [
    "Испытываю напряжение, тревожность.",
    "Испытываю страх, ожидание несчастья.",
    "Тревожат беспокойные мысли.",
    "Могу легко расслабиться.",
    "Испытываю внутренний дискомфорт, дрожь, напряжение.",
    "Беспокоит неусидчивость, я постоянно нахожусь в движении.",
    "Испытываю внезапное чувство паники."
]

ANXIETY_OPTIONS = [
    ["Постоянно", "Часто", "Иногда", "Не испытываю"],
    ["Испытываю сильный страх", "Страх есть, но он не велик", "Иногда", "Не испытываю"],
    ["Постоянно", "Очень часто", "Иногда", "Не тревожат"],
    ["Расслабиться не могу", "Могу расслабиться очень редко", "Наверное, могу расслабиться", "Могу расслабиться"],
    ["Очень часто", "Часто", "Иногда", "Никогда не испытываю"],
    ["Постоянно", "Наверное, это так", "Частично это так", "Не беспокоит"],
    ["Очень часто", "Часто", "Редко", "Не испытываю чувство паники"]
]

ANXIETY_SCORES = [
    [3, 2, 1, 0],
    [3, 2, 1, 0],
    [3, 2, 1, 0],
    [3, 2, 1, 0],
    [3, 2, 1, 0],
    [3, 2, 1, 0],
    [3, 2, 1, 0]
]

TEST_TYPES = {
    "demographic": {
        "name": "Демографические данные",
        "questions": DEMOGRAPHIC_QUESTIONS,
        "options": DEMOGRAPHIC_OPTIONS,
        "scores": [],
        "total_questions": len(DEMOGRAPHIC_QUESTIONS)
    },
    "depression": {
        "name": "Госпитальная шкала депрессии HADS",
        "questions": DEPRESSION_QUESTIONS,
        "options": DEPRESSION_OPTIONS,
        "scores": DEPRESSION_SCORES,
        "total_questions": len(DEPRESSION_QUESTIONS),
        "format_by_gender": True  
    },
    "anxiety": {
        "name": "Шкала тревоги Бека (BAI)",
        "questions": ANXIETY_QUESTIONS,
        "options": ANXIETY_OPTIONS,
        "scores": ANXIETY_SCORES,
        "total_questions": len(ANXIETY_QUESTIONS)
    }
}


# Function to get formatted questions and answer options
def get_formatted_test(test_type, user_gender=None):
    """
    Возвращает отформатированные вопросы и варианты ответов для указанного типа теста
    """
    test_info = TEST_TYPES[test_type]

    # If the test does not require gender formatting or gender is not specified
    if not test_info.get("format_by_gender", False) or user_gender is None:
        return test_info["questions"], test_info["options"]

    # Formatting questions
    formatted_questions = []
    for question in test_info["questions"]:
        formatted_questions.append(format_gender_specific_text(question, user_gender))

    # Formatting answer options
    formatted_options = []
    for options_list in test_info["options"]:
        formatted_options_list = [format_gender_specific_text(option, user_gender) for option in options_list]
        formatted_options.append(formatted_options_list)

    return formatted_questions, formatted_options
