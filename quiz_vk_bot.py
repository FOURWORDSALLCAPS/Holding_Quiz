import vk_api as vk
import random
import redis
import argparse

from environs import Env
from questions_and_answers import get_questions_and_answers, get_answer
from vk_api.longpoll import VkLongPoll, VkEventType
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
from vk_api.utils import get_random_id


def start(event, vk_api) -> None:
    keyboard = VkKeyboard(one_time=True)
    keyboard.add_button('Новый вопрос', color=VkKeyboardColor.POSITIVE)
    keyboard.add_button('Сдаться', color=VkKeyboardColor.NEGATIVE)
    keyboard.add_line()
    keyboard.add_button('Мой счёт', color=VkKeyboardColor.PRIMARY)

    vk_api.messages.send(
        user_id=event.user_id,
        random_id=get_random_id(),
        keyboard=keyboard.get_keyboard(),
        message=f'Привет\nЯ бот для викторин'
    )


def ask_new_question(event, vk_api, questions_and_answers, redis_connection, keyboard) -> None:
    random_question = random.choice(list(questions_and_answers.keys()))
    redis_connection.set(event.user_id, random_question)
    vk_api.messages.send(
        user_id=event.user_id,
        random_id=get_random_id(),
        keyboard=keyboard.get_keyboard(),
        message=random_question
    )


def attempt_answer(event, vk_api, questions_and_answers, redis_connection, keyboard) -> None:
    question = redis_connection.get(event.user_id)
    answer = get_answer(questions_and_answers[question])
    user_answer = event.text
    if user_answer.lower() == answer.lower():
        vk_api.messages.send(
            user_id=event.user_id,
            random_id=get_random_id(),
            keyboard=keyboard.get_keyboard(),
            message="Правильно! Поздравляю! Для следующего вопроса нажми «Новый вопрос»."
        )
    else:
        vk_api.messages.send(
            user_id=event.user_id,
            random_id=get_random_id(),
            keyboard=keyboard.get_keyboard(),
            message="Неправильно… Попробуешь ещё раз?"
        )


def admit_defeat(event, vk_api, questions_and_answers, redis_connection, keyboard) -> None:
    question = redis_connection.get(event.user_id)
    answer = get_answer(questions_and_answers[question])
    vk_api.messages.send(
        user_id=event.user_id,
        random_id=get_random_id(),
        keyboard=keyboard.get_keyboard(),
        message=f"Неплохо! Вот правильный ответ: {answer}"
    )
    ask_new_question(event, vk_api, questions_and_answers, redis_connection, keyboard)


def main():
    parser = argparse.ArgumentParser(description='Данный код позволяет записать вопросы и ответы из файла',
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('--dest_folder', type=str, default='quiz_questions/ierusa11.txt',
                        help='Путь к файлу с вопросами и ответами')
    args = parser.parse_args()
    env = Env()
    env.read_env()
    vk_group_token = env("VK_GROUP_TOKEN")
    redis_host = env('REDIS_HOST')
    redis_port = env('REDIS_PORT')
    redis_password = env('REDIS_PASSWORD')
    redis_connection = redis.Redis(
        host=redis_host,
        port=redis_port,
        password=redis_password,
        decode_responses=True,
    )
    questions_and_answers = get_questions_and_answers(args.dest_folder)
    keyboard = VkKeyboard(one_time=True)
    keyboard.add_button('Новый вопрос', color=VkKeyboardColor.POSITIVE)
    keyboard.add_button('Сдаться', color=VkKeyboardColor.NEGATIVE)
    keyboard.add_line()
    keyboard.add_button('Мой счёт', color=VkKeyboardColor.PRIMARY)
    vk_session = vk.VkApi(token=vk_group_token)
    vk_api = vk_session.get_api()
    longpoll = VkLongPoll(vk_session)
    for event in longpoll.listen():
        if event.type == VkEventType.MESSAGE_NEW and event.to_me:
            if event.text == "start":
                start(event, vk_api)
            elif event.text == "Новый вопрос":
                ask_new_question(event, vk_api, questions_and_answers, redis_connection, keyboard)
            elif event.text == "Сдаться":
                admit_defeat(event, vk_api, questions_and_answers, redis_connection, keyboard)
            else:
                attempt_answer(event, vk_api, questions_and_answers, redis_connection, keyboard)


if __name__ == "__main__":
    main()
