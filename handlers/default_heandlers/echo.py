from loader import bot
from telebot.types import Message


@bot.message_handler(content_types=['text'])
def echo(message: Message):
    bot.reply_to(message, f'Не понимаю сообщение: {message.text}')