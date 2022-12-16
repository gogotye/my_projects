import json
from database.hotels_data import hotels_data
from database.users_data import users
from loader import bot
from telebot.types import Message, InputMediaPhoto
from utils.request_func import search_request, search_id, list_request, detail_request, func, save_hotel_data, \
    display_hotel_info
from config_data.config import RAPID_API_KEY


def high_price_send_data(message: Message) -> None:
    hotels = users[message.from_user.id]["hotels_limit"]
    count = 0
    bot.send_message(message.chat.id, 'Идёт сбор данных пожалуйста подождите...')
    bot.send_message(message.chat.id, f'Прогресс по отелям: {count} из {hotels}')

    search_res = search_request(city=users[message.from_user.id]['city'],
                                key=RAPID_API_KEY)
    users[message.from_user.id]['city_id'] = search_id(search_res)

    list_res = list_request(check_in_date=users[message.from_user.id]['check_in'],
                            check_out_date=users[message.from_user.id]['check_out'],
                            region_id=users[message.from_user.id]['city_id'],
                            hotels_limit=hotels,
                            sort='RECOMMENDED',
                            key=RAPID_API_KEY)

    sort_list = []
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
            lst = (
                [(k[0], k[1]) for k in data[6]] if len(hotels_data[id]['images']) > 10 else [InputMediaPhoto(media=p[0])
                                                                                             for p in data[6]]) \
                if flag else []

        hotels_data[id] = save_hotel_data(cur_hotel_data=data, flag=flag)

        sort_list.append((hotels_data[id], lst))

        count += 1
        bot.send_message(message.chat.id, f'Прогресс по отелям: {count} из {hotels}')

    sort_list.sort(key=lambda x: x[0]['per_night'], reverse=True)

    for elem in sort_list:
        try:
            if flag and 0 < len(elem[1]) <= 10:
                bot.send_message(message.chat.id, display_hotel_info(hotel_data=elem[0]))
                bot.send_media_group(chat_id=message.chat.id, media=elem[1], disable_notification=True)
            elif flag and len(elem[1]) > 10:
                bot.send_message(message.chat.id, display_hotel_info(hotel_data=elem[0]))
                for url, description in elem[1]:
                    bot.send_message(message.chat.id, description, disable_notification=True)
                    bot.send_photo(chat_id=message.chat.id, photo=url, disable_notification=True)
            else:
                bot.send_message(message.chat.id, display_hotel_info(hotel_data=elem[0]))
        except Exception as ex:
            pass

    sort_list.clear()
