from telebot.types import ReplyKeyboardMarkup, KeyboardButton


def keyboard() -> ReplyKeyboardMarkup:
    keyboard = ReplyKeyboardMarkup(True, one_time_keyboard=True)
    keyboard.add(KeyboardButton('Да'))
    keyboard.add(KeyboardButton('Нет'))
    return keyboard


def keyboard_2() -> ReplyKeyboardMarkup:
    keyboard = ReplyKeyboardMarkup(True, one_time_keyboard=True)
    keyboard.add(KeyboardButton('Все данные введены правильно'))
    keyboard.add(KeyboardButton('Начать заново'))
    return keyboard