import logging
import random
import redis

from environs import Env
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackContext, ConversationHandler, MessageHandler, Filters
from questions_and_answers import get_questions_and_answers, get_answer

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

logger = logging.getLogger(__name__)


def start(update: Update, context: CallbackContext) -> str:
    """Send a message when the command /start is issued."""
    buttons = [["Новый вопрос", "Сдаться"], ["Мой счёт"]]
    keyboard = ReplyKeyboardMarkup(buttons)
    context.bot.send_message(
        chat_id=update.message.chat_id,
        text=f'Привет\nЯ бот для викторин',
        reply_markup=keyboard,
    )

    return 'SELECTING_FEATURE'


def stop(update: Update, context: CallbackContext) -> None:
    """End Conversation by command."""
    update.message.reply_text('До встречи')


def ask_new_question(update: Update, context: CallbackContext, redis_connection, questions_and_answers) -> str:
    random_question = random.choice(list(questions_and_answers.keys()))
    redis_connection.set(update.message.chat_id, random_question)
    update.message.reply_text(random_question)

    return 'NEW_QUESTIONS'


def attempt_answer(update: Update, context: CallbackContext, redis_connection, questions_and_answers) -> str:
    question = redis_connection.get(update.message.chat_id)
    answer = get_answer(questions_and_answers[question])
    user_answer = update.message.text
    if user_answer.lower() == answer.lower():
        update.message.reply_text("Правильно! Поздравляю! Для следующего вопроса нажми «Новый вопрос».")

        return 'SELECTING_FEATURE'
    else:
        update.message.reply_text("Неправильно… Попробуешь ещё раз?")


def admit_defeat(update: Update, context: CallbackContext, redis_connection, questions_and_answers) -> None:
    question = redis_connection.get(update.message.chat_id)
    answer = get_answer(questions_and_answers[question])
    update.message.reply_text(f"Неплохо! Вот правильный ответ: {answer}")
    ask_new_question(update, context, redis_connection, questions_and_answers)


def main() -> None:
    """Start the bot."""
    env = Env()
    env.read_env()
    tg_bot_token = env('TG_BOT_TOKEN')
    redis_host = env('REDIS_HOST')
    redis_port = env('REDIS_PORT')
    redis_password = env('REDIS_PASSWORD')
    updater = Updater(tg_bot_token)
    redis_connection = redis.Redis(
        host=redis_host,
        port=redis_port,
        password=redis_password,
        decode_responses=True,
    )
    questions_and_answers = get_questions_and_answers()
    dispatcher = updater.dispatcher
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            'SELECTING_FEATURE': [
                MessageHandler(
                    Filters.regex('^Новый вопрос$'),
                    lambda update, context: ask_new_question(update, context, redis_connection, questions_and_answers)
                ),
            ],
            'NEW_QUESTIONS': [
                MessageHandler(
                    Filters.regex('^Новый вопрос$'),
                    lambda update, context: ask_new_question(update, context, redis_connection, questions_and_answers)
                ),
                MessageHandler(
                    Filters.regex('^Сдаться$'),
                    lambda update, context: admit_defeat(update, context, redis_connection, questions_and_answers)
                ),
                MessageHandler(
                    Filters.text & ~Filters.command,
                    lambda update, context: attempt_answer(update, context, redis_connection, questions_and_answers)
                ),
            ]
        },
        fallbacks=[CommandHandler('stop', stop)],
    )

    dispatcher.add_handler(conv_handler)
    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
