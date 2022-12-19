import json
from database.hotels_data import hotels_data
from database.users_data import users
from loader import bot
from telebot.types import Message, InputMediaPhoto, ReplyKeyboardRemove
from utils.request_func import list_request, detail_request, func, \
    save_hotel_data, display_final_info, empty_or_not
from config_data.config import RAPID_API_KEY


def low_price_send_data(message: Message) -> None:
    count = 0
    hotels = users[message.from_user.id]["hotels_limit"]
    bot.send_message(message.chat.id, 'Идёт сбор данных пожалуйста подождите...', reply_markup=ReplyKeyboardRemove())
    bot.send_message(message.chat.id, f'Прогресс по отелям: {count} из {hotels}')

    list_res = list_request(check_in_date=users[message.from_user.id]['check_in'],
                            check_out_date=users[message.from_user.id]['check_out'],
                            region_id=users[message.from_user.id]['city_id'],
                            hotels_limit=users[message.from_user.id]['hotels_limit'],
                            sort='PRICE_LOW_TO_HIGH',
                            key=RAPID_API_KEY)

    final_list = []
    flag = True if 'photo_limit' in users[message.from_user.id] else False
    imgs = users[message.from_user.id]['photo_limit'] if flag else None

    list_res = json.loads(list_res)
    for i in list_res['data']['propertySearch']['properties']:
        id = i['id']
        hotels_data[id] = {}

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

    empty_or_not(message=message, lst=final_list)

    for elem in final_list:
        display_final_info(message=message, flag=flag, hotel_info=elem[0], photo_info=elem[1])

    final_list.clear()