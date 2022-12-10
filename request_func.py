from typing import Any, List, Tuple
import requests
import re


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
        return Exception('Проблема с соединением')
    else:
        if res.status_code == requests.codes.ok:
            return res.text
        return ConnectionError('Код ответа не равен 200')


def list_request(check_in_date: str, check_out_date: str, region_id: int, hotels_limit: int, key: str) -> Any:

    check_in_date, check_out_date = map(int, check_in_date.split('-')), map(int, check_out_date.split('-'))

    lst_in, lst_out = [i for i in check_in_date], [k for k in check_out_date]

    url = "https://hotels4.p.rapidapi.com/properties/v2/list"
    payload = {
        "currency": "USD",
        "eapid": 1,
        "locale": "",
        "siteId": 300000001,
        "destination": {"regionId":region_id},
        "checkInDate": {
            "day": lst_in[2],
            "month": lst_in[1],
            "year": lst_in[0]
        },
        "checkOutDate": {
            "day": lst_out[2],
            "month": lst_out[1],
            "year": lst_in[0]
        },
        "rooms": [
            {
                "adults": 1
            }
        ],
        "resultsStartingIndex": 0,
        "resultsSize": int(hotels_limit),
        "sort": "PRICE_LOW_TO_HIGH",
        "filters": {"price": {
            "max": "",
            "min": ""
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
        return Exception('Проблема с соединением')
    else:
        if response.status_code == requests.codes.ok:
            return response.text
        return ConnectionError('Код ответа не равен 200')


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
        return Exception('Проблема с соединением')
    else:
        if response.status_code ==requests.codes.ok:
            return response.text
        return ConnectionError('Код ответа не равен 200')


def recurs(res: Any, to_find: list) -> str:
    if isinstance(res, dict):
        for i in res:
            if isinstance(res[i], dict) or isinstance(res[i], list):
                resul = recurs(res[i], to_find)
                if resul:
                    return resul
            else:
                if i in to_find:
                    return res[i]
    elif isinstance(res, list):
        for k in res:
            resul = recurs(k, to_find)
            if resul:
                return resul


def recurs_for_images(res: Any, to_find: list, images: int, lst=[]) -> List[Tuple[str, str]]:
    if isinstance(res, dict):
        for i in res:
            if isinstance(res[i], dict) or isinstance(res[i], list):
                func = recurs_for_images(res[i], to_find, images, lst=[])
                if func:
                    lst.extend(func)
            else:
                if i in to_find:
                    return [(res[i], res['description'])]
    elif isinstance(res, list):
        for k in res:
            func_2 = recurs_for_images(k, to_find, images, lst=[])
            if func_2:
                lst.extend(func_2)
                if len(lst) == images:
                    return lst
    return lst


def search_id(text: str) -> str:
    match = re.search(r'\WgaiaId\W*(\d+)\W[\w\W]*\Wtype\W*CITY\W', text)
    return match.group(1)

