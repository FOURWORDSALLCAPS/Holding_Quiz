import logging
import random

from environs import Env
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackContext, ConversationHandler, MessageHandler, Filters
from questions_and_answers import get_questions_and_answers

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

logger = logging.getLogger(__name__)


def start(update: Update, context: CallbackContext) -> str:
    """Send a message when the command /start is issued."""
    user = update.effective_user
    buttons = [["Новый вопрос", "Сдаться"], ["Мой счёт"]]
    keyboard = ReplyKeyboardMarkup(buttons)
    context.bot.send_message(
        chat_id=update.message.chat_id,
        text=f'Привет {user.mention_markdown_v2()}\nЯ бот для викторин',
        reply_markup=keyboard,
    )

    return 'SELECTING_FEATURE'


def stop(update: Update, context: CallbackContext) -> None:
    """End Conversation by command."""
    update.message.reply_text('До встречи')


def ask_new_question(update: Update, context: CallbackContext) -> str:
    questions_and_answers = get_questions_and_answers()
    random_question = random.choice(list(questions_and_answers.keys()))
    formatted_question = '\n'.join(line.strip() for line in random_question.split('\n')[1:])
    update.message.reply_text(formatted_question)

    return 'SELECTING_QUESTIONS'


def main() -> None:
    """Start the bot."""
    env = Env()
    env.read_env()
    tg_bot_token = env('TG_BOT_TOKEN')
    updater = Updater(tg_bot_token)
    dispatcher = updater.dispatcher

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            'SELECTING_FEATURE': [
                MessageHandler(
                    Filters.regex('^Новый вопрос$'),
                    ask_new_question,
                ),
            ],
        },
        fallbacks=[CommandHandler('stop', stop)],
    )

    dispatcher.add_handler(conv_handler)
    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
