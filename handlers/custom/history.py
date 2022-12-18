import sqlite3
from contextlib import closing
from telebot.types import Message
from loader import bot
from utils.request_func import db_answer

path = 'database/history.db'


@bot.message_handler(commands=['history'])
def base(message: Message) -> None:
    create_history_tab(path_to_db=path)
    with closing(sqlite3.connect(path)) as connection:
        with closing(connection.cursor()) as cursor:
            answer = cursor.execute("SELECT userid, command, time, hotels FROM user WHERE userid = ?",
                           (message.from_user.id,)).fetchall()

            if not answer:
                bot.send_message(message.chat.id, 'Вы ещё ничего не искали')
            else:
                for i in answer:
                    bot.send_message(message.chat.id, db_answer(i))


def create_history_tab(path_to_db: str = path):
    with closing(sqlite3.connect(path_to_db)) as connection:
        with closing(connection.cursor()) as cursor:
            cursor.execute("CREATE TABLE IF NOT EXISTS user(userid INTEGER, command TEXT, time TEXT, hotels TEXT)")
            connection.commit()


def add_value(data: tuple, path_to_db: str = path):
    create_history_tab(path_to_db=path)
    with closing(sqlite3.connect(path_to_db)) as connection:
        with closing(connection.cursor()) as cursor:
            cursor.execute("INSERT INTO user VALUES(?, ?, ?, ?);", data)
            connection.commit()
