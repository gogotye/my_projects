import telebot


bot = telebot.TeleBot('5985504927:AAERqsZb4E81F7BX1UL4Q8xYLQJtE-XekKs')


@bot.message_handler(commands=['hello-world', 'help'])
def ans_command(message):
    if message.text.lower() == '/hello-world':
        bot.send_message(message.chat.id, 'Мир всесторонне тебя приветствует! 😁')
    elif message.text.lower() == '/help':
        bot.send_message(message.chat.id, f' Список доступных команд: \n{"/hello-world"} \n{"/help"}')


@bot.message_handler(content_types=['text'])
def ans_message(message):
    if message.text.lower() == 'привет':
        bot.send_message(message.from_user.id, f'Привет, меня зовут {bot.get_me().first_name}, мой ник'
                                               f' @{bot.get_me().username}')


bot.infinity_polling()
