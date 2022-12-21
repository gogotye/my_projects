import json
import re
from config_data.config import RAPID_API_KEY
from database.hotels_data import hotels_data
from database.users_data import users
from loader import bot
from telebot.types import Message, InputMediaPhoto, ReplyKeyboardRemove
from utils.request_func import list_request, detail_request, display_user_info, func, \
    save_hotel_data, display_final_info, empty_or_not
from states.user_info import Info
from keyboards.reply.keyboard import keyboard_2
from utils.variables import check_number_for_distance, static_number_of_cities


@bot.message_handler(state=Info.min_distance)
def min_distance(message: Message) -> None:
    if re.fullmatch(check_number_for_distance, message.text):
        users[message.from_user.id]['min_distance'] = float(message.text)
        bot.set_state(message.from_user.id, Info.max_distance, message.chat.id)
        bot.send_message(message.chat.id, 'Ответ записан.\n'
                                          'Введите максимальную дистанцию от центра\n'
                                          'Может быть целое или дробное число через точку\n'
                                          'Например: 1 или 0.23')
    else:
        bot.send_message(message.chat.id, f'Число {message.text} не валидно, попробуйте снова')


@bot.message_handler(state=Info.max_distance)
def max_distance(message: Message) -> None:
    if not re.fullmatch(check_number_for_distance, message.text):
        bot.send_message(message.chat.id, f'Число {message.text} не валидно, попробуйте снова')
    elif users[message.from_user.id]['min_distance'] > float(message.text):
        bot.send_message(message.chat.id, 'Минимальная дистанция не может быть больше максимальной.\nПопробуйте снова')
    else:
        users[message.from_user.id]['max_distance'] = float(message.text)
        bot.set_state(message.from_user.id, Info.min_price, message.chat.id)
        bot.send_message(message.chat.id, 'Ответ записан.\n'
                                          'Введите минимальную желаемую цену')


@bot.message_handler(state=Info.min_price)
def min_price(message: Message):
    if not message.text.isdigit():
        bot.send_message(message.chat.id, 'Цена должна быть числом')
    else:
        users[message.from_user.id]['min_price'] = int(message.text)
        bot.set_state(message.from_user.id, Info.max_price, message.chat.id)
        bot.send_message(message.chat.id, 'Ответ записан.\nВведите максимальную цену')


@bot.message_handler(state=Info.max_price)
def max_price(message: Message):
    if not message.text.isdigit():
        bot.send_message(message.chat.id, 'Цена должна быть числом')
    elif users[message.from_user.id]['min_price'] >= int(message.text):
        bot.send_message(message.chat.id, 'Минимальная цена не может быть больше или равна максимальной')
    else:
        users[message.from_user.id]['max_price'] = int(message.text)
        bot.send_message(message.chat.id, display_user_info(user_data=users[message.from_user.id]),
                         reply_markup=keyboard_2())

        bot.delete_state(message.from_user.id, message.chat.id)


def bestdeal_send_data(message: Message) -> None:
    hotels = users[message.from_user.id]["hotels_limit"]
    count = 0
    bot.send_message(message.chat.id, 'Идёт сбор данных пожалуйста подождите...', reply_markup=ReplyKeyboardRemove())
    bot.send_message(message.chat.id, f'Прогресс по отелям: {count} из {hotels}')

    list_res = list_request(check_in_date=users[message.from_user.id]['check_in'],
                            check_out_date=users[message.from_user.id]['check_out'],
                            region_id=users[message.from_user.id]['city_id'],
                            hotels_limit=static_number_of_cities,
                            sort='DISTANCE',
                            key=RAPID_API_KEY,
                            max_price=users[message.from_user.id]['max_price'],
                            min_price=users[message.from_user.id]['min_price'])

    final_list = []
    flag = True if 'photo_limit' in users[message.from_user.id] else False
    imgs = users[message.from_user.id]['photo_limit'] if flag else None

    list_res = json.loads(list_res)
    for i in list_res['data']['propertySearch']['properties']:
        id = i['id']

        dist = i['destinationInfo']['distanceFromDestination']['value']

        if users[message.from_user.id]['min_distance'] > dist or users[message.from_user.id]['max_distance'] < dist:
            continue

        detail_res = detail_request(id_hotel=id, key=RAPID_API_KEY)
        detail_res = json.loads(detail_res)

        data = func(hotel_info=i, hotel_detail=detail_res, check=flag,
                    photo=imgs)

        hotels_data[id] = save_hotel_data(cur_hotel_data=data, flag=flag)

        lst = []
        if flag:
            lst = [InputMediaPhoto(media=p[0]) for p in data[6]] if flag else []

        final_list.append((hotels_data[id], lst))
        count += 1
        bot.send_message(message.chat.id, f'Прогресс по отелям: {count} из {hotels}')

        if len(final_list) == int(users[message.from_user.id]['hotels_limit']):
            break

    empty_or_not(message=message, lst=final_list)

    final_list.sort(key=lambda x: x[0]['from_center'][0])

    for elem in final_list:
        display_final_info(message=message, flag=flag, hotel_info=elem[0], photo_info=elem[1])

    final_list.clear()

