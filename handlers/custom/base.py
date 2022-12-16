from database.hotels_data import hotels_data
from database.users_data import users
from handlers.custom.lowprice import low_price_send_data
from handlers.custom.highprice import high_price_send_data
from handlers.custom.history import add_value
from loader import bot
from utils.request_func import display_user_info, from_dict_to_str, time
from states.user_info import Info
from telebot.types import Message
from keyboards.reply.keyboard import keyboard, keyboard_2
import re
from handlers.custom import bestdeal
from datetime import datetime


@bot.message_handler(commands=['lowprice', 'highprice', 'bestdeal'])
def base(message: Message) -> None:
    users[message.from_user.id] = {'command': message.text, 'time': time()}
    bot.set_state(message.from_user.id, Info.city, message.chat.id)
    bot.send_message(message.chat.id, 'В каком городе вы хотели бы найти отель?')


@bot.message_handler(state=Info.city)
def city(message: Message) -> None:
    if not re.fullmatch(r'[A-Z][a-z]+(?:[-\s]?[A-Z][a-z]+)*', message.text):
        bot.send_message(message.chat.id, 'Некоректное название города')
    else:
        bot.send_message(message.chat.id, 'Сколько вы бы хотели вывести отелей?\n'
                                          'Максимум 50')
        bot.set_state(message.from_user.id, Info.hotels_limit, message.chat.id)
        users[message.from_user.id]['city'] = message.text


@bot.message_handler(state=Info.hotels_limit)
def hotels(message: Message) -> None:
    if not message.text.isdigit():
        bot.send_message(message.chat.id, 'Введите число, пожалуйста')
    elif int(message.text) > 50:
        bot.send_message(message.chat.id, 'Не больше 50')
    else:
        bot.send_message(message.chat.id, 'Пожалуйста, введите дату въезда в отель.\nФормат: YYYY-MM-DD')
        bot.set_state(message.from_user.id, Info.check_in, message.chat.id)
        users[message.from_user.id]['hotels_limit'] = int(message.text)


@bot.message_handler(state=Info.check_in)
def check_in(message):
    match = re.fullmatch(r'\d{4}-\d{2}-\d{2}', message.text)
    try:
        if not match:
            bot.send_message(message.chat.id, 'Неверный формат даты, попробуйте снова')
        elif datetime.strptime(match.group(), '%Y-%m-%d'):
            bot.set_state(message.from_user.id, Info.check_out, message.chat.id)
            users[message.from_user.id]['check_in'] = message.text
            bot.send_message(message.chat.id, 'Хорошо!\nТеперь нужно ввести дату выезда из отеля.\n'
                                              'Формат: YYYY-MM-DD')
    except ValueError:
        bot.send_message(message.chat.id, 'Введите существующую дату')


@bot.message_handler(state=Info.check_out)
def check_out(message):
    match = re.fullmatch(r'\d{4}-\d{2}-\d{2}', message.text)
    try:
        if not match:
            bot.send_message(message.chat.id, 'Неверный формат даты, попробуйте снова')
        elif datetime.strptime(match.group(), '%Y-%m-%d'):
            check_out = datetime.strptime(match.group(), '%Y-%m-%d')
            check_in_date = datetime.strptime(users[message.from_user.id]['check_in'], '%Y-%m-%d')
            if (check_out.year >
                check_in_date.year) or (check_out.year == check_in_date.year and check_out.month >
                                        check_in_date.month) or (check_out.year == check_in_date.year
                                                                 and check_out.month == check_in_date.month
                                                                 and check_out.day > check_in_date.day):
                bot.send_message(message.chat.id, 'Отлично!\nХотите вывести фотографии отелей?\n',
                                 reply_markup=keyboard())
                bot.set_state(message.from_user.id, Info.req_photo, message.chat.id)
                users[message.from_user.id]['check_out'] = message.text
            else:
                bot.send_message(message.chat.id, 'Дата выезда не может быть в день приезда или раньше него')
    except ValueError:
        bot.send_message(message.chat.id, 'Введите существующую дату')


@bot.message_handler(state=Info.req_photo)
def photo(message: Message) -> None:
    if message.text == 'Да':
        bot.set_state(message.from_user.id, Info.photo_limit, message.chat.id)
        bot.send_message(message.chat.id, 'Сколько вы хотите вывести фотографий?\n'
                                          'Максимум 30')
    elif message.text == 'Нет' and users[message.from_user.id]['command'] == '/bestdeal':
        bot.set_state(message.from_user.id, Info.min_distance, message.chat.id)
        bot.send_message(message.chat.id, 'Укажите минимальную дистанцию от центра\n'
                                          'Может быть целое или дробное число через точку\n'
                                          'Например: 1 или 0.23')
    elif message.text == 'Нет':
        bot.send_message(message.chat.id, display_user_info(user_data=users[message.from_user.id]),
                         reply_markup=keyboard_2())
        bot.delete_state(message.from_user.id, message.chat.id)
    else:
        bot.send_message(message.chat.id, f'{message.from_user.first_name}, нажмите кнопку "Да" или "Нет"')


@bot.message_handler(state=Info.photo_limit)
def get_photo(message: Message) -> None:
    if not message.text.isdigit():
        bot.send_message(message.chat.id, 'Кол-во фотографий должно быть числом')
    elif int(message.text) > 30:
        bot.send_message(message.chat.id, 'Не больше 30 фотографий')
    elif users[message.from_user.id]['command'] == '/bestdeal':
        users[message.from_user.id]["photo_limit"] = int(message.text)
        bot.set_state(message.from_user.id, Info.min_distance, message.chat.id)
        bot.send_message(message.chat.id, 'Укажите минимальную дистанцию от центра\n'
                                          'Может быть целое или дробное число через точку\n'
                                          'Например: 1 или 0.23')
    else:
        users[message.from_user.id]["photo_limit"] = int(message.text)
        bot.send_message(message.chat.id, display_user_info(users[message.from_user.id]),
                         reply_markup=keyboard_2())
        bot.delete_state(message.from_user.id, message.chat.id)


@bot.message_handler(func=lambda message: message.text == 'Все данные введены правильно'
                     or message.text == 'Начать заново')
def send_data(message: Message) -> None:
    if message.text == 'Все данные введены правильно':
        try:
            if users[message.from_user.id]['command'] == '/lowprice':
                low_price_send_data(message=message)
            elif users[message.from_user.id]['command'] == '/highprice':
                high_price_send_data(message=message)
            elif users[message.from_user.id]['command'] == '/bestdeal':
                bestdeal.bestdeal_send_data(message=message)
        except Exception as ex:
            bot.send_message(message.chat.id, 'Что-то пошло не так 😢')
            raise Exception(ex)
        else:
            hotels_name = from_dict_to_str(hotels=hotels_data) if hotels_data else "Ничего не найдено"
            add_value(data=(message.from_user.id,
                            users[message.from_user.id]['command'],
                            users[message.from_user.id]['time'],
                            hotels_name))
            users.clear()
            hotels_data.clear()

    elif message.text == 'Начать заново':
        bot.send_message(message.chat.id, f'Используйте команду {users[message.from_user.id]["command"]}')

