from datetime import datetime
from typing import Any, List, Tuple
import requests
import re

from telebot.types import Message

from database.users_data import users
from loader import bot


def search_request(city: str, key: str) -> Any:
    url = 'https://hotels4.p.rapidapi.com/locations/v3/search'
    querystring = {"q": city}

    headers = {
        "X-RapidAPI-Key": key,
        "X-RapidAPI-Host": "hotels4.p.rapidapi.com"
    }

    try:
        res = requests.request("GET", url, headers=headers, params=querystring)
    except Exception:
        raise Exception('Проблема с соединением')
    else:
        if res.status_code == requests.codes.ok:
            return res.text
        raise ConnectionError('Код ответа не равен 200')


def list_request(check_in_date: str, check_out_date: str, region_id: int, hotels_limit: int, sort: str, key: str,
                 max_price="", min_price="") -> Any:

    check_in_date, check_out_date = map(int, check_in_date.split('-')), map(int, check_out_date.split('-'))

    lst_in, lst_out = [i for i in check_in_date], [k for k in check_out_date]

    url = "https://hotels4.p.rapidapi.com/properties/v2/list"
    payload = {
        "currency": "USD",
        "eapid": 1,
        "locale": "",
        "siteId": 300000001,
        "destination": {"regionId": region_id},
        "checkInDate": {
            "day": lst_in[2],
            "month": lst_in[1],
            "year": lst_in[0]
        },
        "checkOutDate": {
            "day": lst_out[2],
            "month": lst_out[1],
            "year": lst_out[0]
        },
        "rooms": [
            {
                "adults": 1
            }
        ],
        "resultsStartingIndex": 0,
        "resultsSize": hotels_limit,
        "sort": sort,
        "filters": {"price": {
            "max": max_price,
            "min": min_price
        }}
    }
    headers = {
        "content-type": "application/json",
        "X-RapidAPI-Key": key,
        "X-RapidAPI-Host": "hotels4.p.rapidapi.com"
    }
    try:
        response = requests.request("POST", url, json=payload, headers=headers)
    except Exception:
        raise Exception('Проблема с соединением')
    else:
        if response.status_code == requests.codes.ok:
            return response.text
        raise ConnectionError('Код ответа не равен 200')


def detail_request(id_hotel: str, key: str) -> Any:
    url = "https://hotels4.p.rapidapi.com/properties/v2/detail"

    payload = {
        "currency": "USD",
        "eapid": 1,
        "locale": "en_US",
        "siteId": 300000001,
        "propertyId": id_hotel
    }
    headers = {
        "content-type": "application/json",
        "X-RapidAPI-Key": key,
        "X-RapidAPI-Host": "hotels4.p.rapidapi.com"
    }
    try:
        response = requests.request("POST", url, json=payload, headers=headers)
    except Exception:
        raise Exception('Проблема с соединением')
    else:
        if response.status_code == requests.codes.ok:
            return response.text
        raise ConnectionError('Код ответа не равен 200')


def search_id(text: str) -> str:
    match = re.search(r'\WgaiaId\W*(\d+)\W[\w\W]*\Wtype\W*CITY\W', text)
    return match.group(1)


def display_user_info(user_data: dict) -> str:
    info_list = []
    for key, val in user_data.items():
        if key == 'city':
            info_list.append(f'Город поиска: {val}')
        elif key == 'check_in':
            info_list.append(f'Дата въезда: {val}')
        elif key == 'check_out':
            info_list.append(f'Дата выезда: {val}')
        elif key == 'hotels_limit':
            info_list.append(f'Кол-во искомых отелей: {val}')
        elif key == 'photo_limit':
            info_list.append(f'Кол-во искомых фотографий: {val}')
        elif key == 'min_distance':
            info_list.append(f'Минимальная дистанция от центра: {val}')
        elif key == 'max_distance':
            info_list.append(f'Максимальная дистанция от центра: {val}')
        elif key == 'min_price':
            info_list.append(f'Нижний диапазон цены: {val}')
        elif key == 'max_price':
            info_list.append(f'Верхний диапазон цены: {val}')
    return '\n'.join(info_list)


def display_hotel_info(hotel_data: dict) -> str:
    info_list = ['=' * 27 + '\n']
    symbol = hotel_data['money']
    for key, val in hotel_data.items():
        if key == 'name':
            info_list.append(f'Название отеля: {val}')
        elif key == 'address':
            info_list.append(f'Адрес: {val}')
        elif key == 'from_center':
            info_list.append(f'Расстояние до центра: {val[0]} {val[1]}')
        elif key == 'per_night':
            info_list.append(f'Цена за одну ночь: {val}{symbol}')
        elif key == 'total':
            info_list.append(f'Итого за всё время пребывания: {val}{symbol}')
    info_list.append('=' * 27 + '\n')
    return '\n'.join(info_list)


def func(hotel_info: dict, hotel_detail: dict, check: bool, photo: int) -> tuple:
    name = hotel_info['name']
    center_ans = hotel_info["destinationInfo"]["distanceFromDestination"]["value"], \
                 hotel_info["destinationInfo"]["distanceFromDestination"]["unit"]
    per_night = round(hotel_info['price']['lead']['amount'], 1), \
                hotel_info['price']['lead']['currencyInfo']['symbol']
    symbol, per_night = per_night[1], per_night[0]
    total = re.search(r'(\d+(?:[.,]?\d*)?)', hotel_info['price']['displayMessages'][1]['lineItems'][0]['value'])
    address = hotel_detail['data']['propertyInfo']['summary']['location']['address']['addressLine']

    if check:
        images_list = []
        count = 0
        for url in hotel_detail['data']['propertyInfo']['propertyGallery']['images']:
            count += 1
            images_list.append((url['image']['url'], url['image']['description']))
            if count == photo:
                return center_ans, name, symbol, per_night, total.group(1), address, images_list

        return center_ans, name, symbol, per_night, total.group(1), address, images_list

    return center_ans, name, symbol, per_night, total.group(1), address


def save_hotel_data(cur_hotel_data: tuple, flag: bool) -> dict:
    hotel_db = {'money': cur_hotel_data[2], 'name': cur_hotel_data[1], 'from_center': cur_hotel_data[0],
                'per_night': cur_hotel_data[3], 'total': cur_hotel_data[4], 'address': cur_hotel_data[5]}
    if flag:
        hotel_db['images'] = cur_hotel_data[6]

    return hotel_db


def from_dict_to_str(hotels: dict) -> Any:
    lst = []
    try:
        for i in hotels:
            lst.append(hotels[i]['name'])
    except KeyError:
        return "Ничего не найдено"
    else:
        return ', '.join(lst)


def time() -> str:
    return datetime.now().strftime('%Y-%m-%d %H:%M:%S')


def db_answer(info: Tuple[int, str, str, str]):
    return f'Команда: {info[1]}\n' \
           f'Время: {info[2]}\n' \
           f'Найденные отели: {info[3]}'


def check_message(message):
    return (
            message.text == 'Все данные введены правильно' or
            message.text == 'Начать заново'
    )


def display_final_info(message: Message, flag: bool, hotel_info: dict, photo_info: list):
    try:
        if flag:
            bot.send_message(message.chat.id, display_hotel_info(hotel_data=hotel_info))
            bot.send_media_group(chat_id=message.chat.id, media=photo_info, disable_notification=True)
        else:
            bot.send_message(message.chat.id, display_hotel_info(hotel_data=hotel_info))
    except Exception:
        pass


def empty_or_not(message: Message, lst: list):
    if len(lst) == 0:
        bot.send_message(message.chat.id, 'Ничего не найдено')
