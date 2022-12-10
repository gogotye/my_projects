import json
from database.hotels_data import hotels_data
from database.users_data import users
from loader import bot
from states.user_info import Info
from telebot.types import Message
from keyboards.reply.keyboard import keyboard, keyboard_2
from request_func import search_request, search_id, list_request, recurs, detail_request, recurs_for_images
from config_data.config import RAPID_API_KEY
import re
from datetime import datetime


@bot.message_handler(commands=['lowprice'])
def low_price(message: Message) -> None:
    users[message.from_user.id] = {}
    bot.set_state(message.from_user.id, Info.city, message.chat.id)
    bot.send_message(message.chat.id, 'В каком городе вы хотели бы найти отель?')


@bot.message_handler(state=Info.city)
def low_price_city(message: Message) -> None:
    if not re.match(r'\D+(?:[-\s]*\D*)*', message.text):
        bot.send_message(message.chat.id, 'Некоректное название города')
    else:
        bot.send_message(message.chat.id, 'Сколько вы бы хотели вывести отелей?\n'
                                          'Максимум 50')
        bot.set_state(message.from_user.id, Info.hotels_limit, message.chat.id)
        users[message.from_user.id]['city'] = message.text


@bot.message_handler(state=Info.hotels_limit)
def low_price_hotels(message: Message) -> None:
    if not message.text.isdigit():
        bot.send_message(message.chat.id, 'Введите число, пожалуйста')
    else:
        bot.send_message(message.chat.id, 'Пожалуйста, введите дату въезда в отель.\nФормат: YYYY-MM-DD')
        bot.set_state(message.from_user.id, Info.check_in, message.chat.id)
        users[message.from_user.id]['hotels_limit'] = message.text


@bot.message_handler(state=Info.check_in)
def low_price_check_in(message):
    match = re.match(r'\d{4}-\d{2}-\d{2}', message.text)
    if match:
        try:
            if datetime.strptime(match.group(), '%Y-%m-%d'):
                bot.send_message(message.chat.id, 'Хорошо!\nТеперь нужно ввести дату выезда из отеля.\n'
                                                  'Формат: YYYY-MM-DD')
                bot.set_state(message.from_user.id, Info.check_out, message.chat.id)
                users[message.from_user.id]['check_in'] = message.text
        except ValueError:
            bot.send_message(message.chat.id, 'Введите существующую дату')
    else:
        bot.send_message(message.chat.id, 'Неверный формат даты, попробуйте снова')


@bot.message_handler(state=Info.check_out)
def low_price_check_out(message):
    match = re.match(r'\d{4}-\d{2}-\d{2}', message.text)
    if match:
        try:
            check_out = datetime.strptime(match.group(), '%Y-%m-%d')
        except ValueError:
            bot.send_message(message.chat.id, 'Введите существующую дату')
        else:
            check_in_date = datetime.strptime(users[message.from_user.id]['check_in'], '%Y-%m-%d')
            if (check_out.year == check_in_date.year and check_out.month >= check_in_date.month and check_out.day > check_in_date.day)\
                    or (check_out.year > check_in_date.year):
                bot.send_message(message.chat.id, 'Отлично!\nХотите вывести фотографии отелей?\n',
                                 reply_markup=keyboard())
                bot.set_state(message.from_user.id, Info.req_photo, message.chat.id)
                users[message.from_user.id]['check_out'] = message.text
            else:
                bot.send_message(message.chat.id, 'Дата выезда не может быть в день приезда или раньше него')
    else:
        bot.send_message(message.chat.id, 'Неверный формат даты, попробуйте снова')


@bot.message_handler(state=Info.req_photo)
def low_price_photo(message: Message) -> None:
    if message.text == 'Да':
        bot.set_state(message.chat.id, Info.photo_limit, message.chat.id)
        bot.send_message(message.chat.id, 'Сколько вы хотите вывести фотографий?\n'
                                          'Максимум 30')
    elif message.text == 'Нет':
        bot.send_message(message.chat.id, f'Ваши данные:\n'
                                          f'Город поиска: {users[message.from_user.id]["city"]}\n'
                                          f'Дата въезда: {users[message.from_user.id]["check_in"]}\n'
                                          f'Дата выезда: {users[message.from_user.id]["check_out"]}\n'
                                          f'Кол-во искомых отелей: {users[message.from_user.id]["hotels_limit"]}\n',
                                          reply_markup=keyboard_2())
        bot.delete_state(message.from_user.id, message.chat.id)

    else:
        bot.send_message(message.chat.id, f'{message.from_user.first_name}, нажмите кнопку "да" или "нет"')


@bot.message_handler(state=Info.photo_limit)
def low_price_get_photo(message: Message) -> None:
    if not message.text.isdigit():
        bot.send_message(message.chat.id, 'Кол-во фотографий должно быть числом')
    else:
        users[message.from_user.id]["photo_limit"] = message.text
        bot.send_message(message.chat.id, f'Ваши данные:\n'
                                          f'Город поиска: {users[message.from_user.id]["city"]}\n'
                                          f'Дата въезда: {users[message.from_user.id]["check_in"]}\n'
                                          f'Дата выезда: {users[message.from_user.id]["check_out"]}\n'
                                          f'Кол-во искомых отелей: {users[message.from_user.id]["hotels_limit"]}\n'
                                          f'Кол-во искомых фотографий: {users[message.from_user.id]["photo_limit"]}\n',
                                          reply_markup=keyboard_2())
        bot.delete_state(message.from_user.id, message.chat.id)


@bot.message_handler(func=lambda message: message.text == 'Все данные введены правильно'
                     or message.text == 'Начать заново')
def low_price_send_data(message: Message) -> None:
    if message.text == 'Все данные введены правильно':
        try:
            search_res = search_request(city=users[message.from_user.id]['city'],
                                        key=RAPID_API_KEY)

            users[message.from_user.id]['city_id'] = search_id(search_res)
            list_res = list_request(check_in_date=users[message.from_user.id]['check_in'],
                                    check_out_date=users[message.from_user.id]['check_out'],
                                    region_id=users[message.from_user.id]['city_id'],
                                    hotels_limit=users[message.from_user.id]['hotels_limit'],
                                    key=RAPID_API_KEY)

            list_res = json.loads(list_res)
            for i in list_res['data']['propertySearch']['properties']:
                id = i['id']
                hotels_data[id] = {}
                flag = True if 'photo_limit' in users[message.from_user.id] else False

                center_ans = recurs(res=i["destinationInfo"], to_find=["value"])
                per_night = recurs(res=i['price']['lead'], to_find=['amount'])
                total = recurs(res=i['price']['displayMessages'], to_find=['value'])[1:4]

                detail_res = detail_request(id_hotel=id, key=RAPID_API_KEY)
                detail_res = json.loads(detail_res)
                address = recurs(res=detail_res['data']['propertyInfo']['summary']['location'], to_find=['addressLine'])
                if flag:
                    images_list = recurs_for_images(res=detail_res['data']['propertyInfo']['propertyGallery'],
                                                    to_find=['url'],
                                                    images=int(users[message.from_user.id]['photo_limit']))

                bot.send_message(message.chat.id, f'Название отеля: {i["name"]}\n'
                                                  f'Адрес: {address}\n'
                                                  f'Расстояние до центра: {center_ans}\n'
                                                  f'Цена за одну ночь: {per_night}$\n'
                                                  f'Итого за всё время пребывания: {total}$\n'
                                 if not flag

                                 else
                                                  f'Название отеля: {i["name"]}\n'
                                                  f'Адрес: {address}\n'
                                                  f'Расстояние до центра: {center_ans}\n'
                                                  f'Цена за одну ночь: {per_night}$\n'
                                                  f'Итого за всё время пребывания: {total}$\n'
                                                  f'Фотографии:')
                if flag:
                    hotels_data[id]['images'] = images_list
                    for k in images_list:
                        bot.send_message(message.chat.id, f'{k[1]}:\n{k[0]}')

                hotels_data[id]['name'] = i['name']
                hotels_data[id]['from_center'] = center_ans
                hotels_data[id]['per_night'] = per_night
                hotels_data[id]['total'] = total
                hotels_data[id]['address'] = address

        except Exception as ex:
            raise Exception(ex)
    elif message.text == 'Начать заново':
        bot.send_message(message.chat.id, 'Используйте команду /lowprice')


