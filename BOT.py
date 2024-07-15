
import telebot
from telebot.types import ReplyKeyboardMarkup
from telebot.types import Message

from DEB import *
from text import *
from config import *
from GPT import create_system_prompt, ask_gpt, promt


logging.basicConfig(
    filename=LOG_name,
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    filemode="w",
)

bot = telebot.TeleBot(TOKEN)

create_db()
create_table()


def create_keyboard(buttons_list: list) -> ReplyKeyboardMarkup:
    keyboard = ReplyKeyboardMarkup(row_width=2, resize_keyboard=True, one_time_keyboard=True)
    keyboard.add(*buttons_list)
    return keyboard

@bot.message_handler(commands=['help'])
def help_com(message: Message):
    bot.send_message(message.from_user.id, help, reply_markup=create_keyboard(['Выбрать жанр']))

@bot.message_handler(commands=['debug'])
def send_logs(message):
    try:
        with open("log_file.txt", "rb") as f:
            bot.send_document(message.chat.id, f)

    except:
        bot.send_message(message.chat.id, 'Не удалось отправить файл')



@bot.message_handler(commands=['start'])
def start_com(message: Message):
    update_row(message.from_user.id, 'messages', json.dumps([]))
    if not is_user_in_db(message.from_user.id):
        if len(get_all_from_table()) < MAX_USERS:
            add_new_user(message.from_user.id)

    elif is_user_in_db(message.from_user.id) and get_user_data(message.from_user.id)['sessions'] < MAX_SESSIONS:
        logging.info(f'Пользователь {message.from_user.id} снова с нами.')

    else:
        bot.send_message(message.from_user.id, text_apolog)
        return

    bot.send_message(message.from_user.id, hello, reply_markup=create_keyboard(['Выбрать жанр', '/help']))


def filter_choose_genre(message: Message) -> bool:
    user_id = message.from_user.id
    if is_user_in_db(user_id):
        return message.text in ["Выбрать жанр", "Начать новую сессию"]


@bot.message_handler(func=filter_choose_genre)
def choose_genre(message: Message):
    user_data = get_user_data(message.from_user.id)
    if user_data['sessions'] < MAX_SESSIONS:
        bot.send_message(message.from_user.id, text_genre, reply_markup=create_keyboard(genre_but))
        update_row(message.from_user.id, 'sessions', user_data['sessions'] + 1)
        update_row(message.from_user.id, 'tokens', MAX_TOKENS)
        update_row(message.from_user.id, 'messages', json.dumps([1]))
        update_row(message.from_user.id, 'additions', None)
        bot.register_next_step_handler(message, remember_genre)
    else:
        bot.send_message(message.from_user.id, text_apolog2)


def remember_genre(message: Message):
    user_answer = message.text
    if user_answer in genre_but:
        update_row(message.from_user.id, 'genre', user_answer)
        bot.send_message(message.from_user.id, imp_hero, reply_markup=create_keyboard(text_hero))
        bot.register_next_step_handler(message, remember_hero)
    else:
        bot.send_message(message.from_user.id, text_genre2, reply_markup=create_keyboard(genre_but))
        bot.register_next_step_handler(message, remember_genre)


def remember_hero(message: Message):
    user_answer = message.text
    if user_answer in hero:
        update_row(message.from_user.id, 'hero', user_answer)
        bot.send_message(message.from_user.id, text_set, reply_markup=create_keyboard(but_settings))
        bot.register_next_step_handler(message, remember_setting)
    else:
        bot.send_message(message.from_user.id, text_hero, reply_markup=create_keyboard(hero))
        bot.register_next_step_handler(message, remember_hero)


def remember_setting(message: Message):
    user_answer = message.text
    if user_answer in but_settings:
        update_row(message.from_user.id, 'setting', user_answer)
        bot.send_message(message.from_user.id, add, reply_markup=create_keyboard(['/start_story']))
        bot.register_next_step_handler(message, remember_additions)
    else:
        bot.send_message(message.from_user.id, text_set2, reply_markup=create_keyboard(but_settings))
        bot.register_next_step_handler(message, remember_setting)


def remember_additions(message: Message):
    user_answer = message.text
    if user_answer != '/start_story':
        update_row(message.from_user.id, 'additions', user_answer)

    bot.send_message(message.from_user.id, start_story, reply_markup=create_keyboard(['/end']))
    bot.register_next_step_handler(message, start_story)


@bot.message_handler(commands=['start_story'])
def start_story(message: Message):
    messages = [
        {'role': 'system', 'text': create_system_prompt(message.from_user.id)},
        {'role': 'user', 'text': message.text}
    ]
    json_messages = json.dumps(messages)
    update_row(message.from_user.id, 'messages', json_messages)
    answer = ask_gpt(message.from_user.id)
    bot.send_message(message.from_user.id, answer)
    messages.append({'role': 'assistant', 'text': answer})
    json_messages = json.dumps(messages)
    update_row(message.from_user.id, 'messages', json_messages)

    def enter_message(message):
        if message.text != '/end':
            a = message.text
            b = promt(system_content , a , assistant_content , answer)
            bot.send_message(message.chat.id, b)
            bot.register_next_step_handler(message, enter_message)
        else:
            bot.send_message(message.chat.id, 'Конец,перевожу в меню',reply_markup=create_keyboard(['Выбрать жанр', '/help']))
    bot.register_next_step_handler(message, enter_message)
bot.polling(non_stop=True)
