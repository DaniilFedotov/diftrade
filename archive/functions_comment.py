import os
import sys

import logging
import time

import requests
from dotenv import load_dotenv
from telegram import TelegramError, Bot
from binance.spot import Spot


VERSIONS = ['Trader_sdk', 'Scalper_sdk', 'Smart_sdk']  # Различные версии бота
COEF = {VERSIONS[0]: {'INLET': 0.9992,
                      'OUTLET': 1.0008,
                      'STOP': 0.98,
                      'STOP_LIMIT': 0.979,
                      'CHECK_T': 60},
        VERSIONS[1]: {'INLET': 5,
                      'OUTLET': 1.0005,
                      'STOP': 0.985,
                      'STOP_LIMIT': 0.984,
                      'CHECK_T': 60},
        VERSIONS[2]: {'INLET': 0.9990,
                      'OUTLET': 1.0025,
                      'STOP': 0.98,
                      'STOP_LIMIT': 0.979,
                      'CHECK_T': 60}}

load_dotenv()  # Загружает секретные ключи

BINANCE_TOKEN = os.getenv('BINANCE_TOKEN_SDK')  # Токен для версии через SDK
BINANCE_KEY = os.getenv('BINANCE_SECRET_KEY_SDK')  # Ключ для версии через SDK
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')  # Токен для управления ботом
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')  # ID чата, в который требуется отправка сообщений

BASE_URL = 'https://api.binance.com'  # Адрес API бинанса
ENDPOINT = '/api/v3/'  # Эндпоинт
ENDPOINT_FUNC = 'ticker/price'  # Функция, в данный момент получение цены по тикеру
HEADERS = {"Authorization": f"OAuth {BINANCE_TOKEN}"}

DEF = {  # DEFINITION, коэф-ты для проверки уровней. Определяют толщину уровня и длину участка
    12: {'hc1': 0.1,  # high_coef снизу от уровня
         'hc2': 0.0,  # high_coef сверху от уровня
         'lc': 0.1,  # low-coef сверху от уровня
         'st': 0,  # start - начало интервала
         'end': 12},  # end - конец интервала
    6: {'hc1': 0.1,
        'hc2': 0.0,
        'lc': 0.1,
        'st': 12,
        'end': 18},
    5: {'hc1': 0.12,
        'hc2': 0.12,
        'lc': 0.1,
        'st': 18,
        'end': 23},
    1: {'hc1': 0.12,
        'hc2': 0.0,
        'lc': 0.06,
        'st': 23,
        'end': 24}
}  # Сумма ключей должна быть равна 24 (часам)

RECVWINDOW = 59000

bot = Bot(token=TELEGRAM_TOKEN)  # Регистрируем Telegram-бота

client = Spot(api_key=BINANCE_TOKEN, api_secret=BINANCE_KEY)  # Регистрируем клиента для API-binance


def get_logger(version):
    """Создает логгер с заданными параметрами и возвращает его."""
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)  # Назначается минимальный уровень, имея который сообщение идет в лог
    handler = logging.StreamHandler(stream=sys.stdout)
    file_handler = logging.FileHandler(f"log_{version}.log", mode='a')  # Обработчик для логирования в файл
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")  # Формат сообщения в лог
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.addHandler(file_handler)
    return logger


def check_level(logger, version, current_price):
    """Проверяет, находится ли цена в допустимом для входа диапазоне."""
    intervals = DEF.keys()  # Содержит в себе нелинейные временные промежутки на таймфрейме
    data = client.klines('BTCTUSD', '1h', limit=24)  # В ответ на API-запрос получает свечи за указанный период
    for interval in intervals:  # Для каждого из временных промежутков
        highs = []
        lows = []
        for data_hour in data[DEF[interval]['st']:DEF[interval]['end']]:  # Для каждого часа из временного промежутка
            highs.append(float(data_hour[2]))  # Добавляем наибольшее значение цены для часа в список
            lows.append(float(data_hour[3]))  # Добавляем наименьшее значение цены для часа в список
        width = max(highs) - min(lows)  # Находим длину коридора для временного промежутка
        if (max(highs) - DEF[interval]['hc1'] * width < current_price < max(highs) + DEF[interval]['hc2'] * width or
                min(lows) < current_price < min(lows) + DEF[interval]['lc'] * width): # Если цена в одном из промежутков
            print(f'width: {width}'
                  f'max2:{max(highs)}'
                  f'curprice:{current_price}'
                  f'max1{max(highs) - DEF[interval]["hc"] * width}')
            print(f'low1:{min(lows)}'
                  f'curprice:{current_price}'
                  f'low2:{min(lows) + DEF[interval]["lc"] * width}')
            logger.debug(f'{version}: Проверены уровни для входа: False')
            return False  # Если цена находится в пределах толщины одного из уровней
    logger.debug(f'{version}: Проверены уровни для входа: True')
    return True  # Если цена не находится в пределах толщины одного из уровней


def check_price(logger, version):
    """Проверяет цену монеты."""
    try:
        price = float(client.ticker_price('BTCTUSD')["price"])  # В ответ на API-запрос получает цену монеты
        logger.debug(f'{version}: Цена проверена: {price} TUSD')
        return price
    except Exception as error:
        message = f'Ошибка при проверке цены: {error}'
        logger.error(message)
        send_message(logger, message)
        raise Exception(message)


def send_message(logger, message):
    """Отправляет сообщение в Telegram чат."""
    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)  # Бот отправляет сообщение в телеграм по указанному ID
        logger.debug(f'Сообщение в Telegram отправлено: {message}')
    except TelegramError:
        logger.error(f'Сбой при отправке сообщения в Telegram: {message}')


def buy_coin(logger, version):
    """Выставляет рыночный ордер на покупку монеты."""
    quote = get_balance(logger, version, 'TUSD')
    params = {
        "symbol": "BTCTUSD",  # Тикер токена
        "side": "BUY",  # Покупка
        "type": "MARKET",  # Тип ордера - рыночный
        "quoteOrderQty": quote,  # Сумма TUSD на ордер
    }
    response = client.new_order(**params)  # Открывает ордер на покупку по рыночной цене
    message = (f'{version}: Куплено {response["origQty"]} BTC на сумму '
               f'{response["cummulativeQuoteQty"]} TUSD по цене {response["fills"][0]["price"]}')
    logger.info(message)
    send_message(logger, message)
    return response


def sell_coin(logger, version, buy_info):
    """Выставляет ОСО ордер на продажу монеты по заданной цене."""
    quantity = float(buy_info['origQty'])
    price = float(buy_info['cummulativeQuoteQty']) / quantity
    sell_price = int(price * COEF[version]['OUTLET'])
    stop_price = int(price * COEF[version]['STOP'])
    stop_limit = int(price * COEF[version]['STOP_LIMIT'])
    print(f'quantity:{quantity}'
          f'price:{price}'
          f'sell_price:{sell_price}'
          f'stop_price:{stop_price}'
          f'stop_limit:{stop_limit}')
    params = {
        "symbol": "BTCTUSD",  # Тикер токена
        "side": "SELL",  # Продажа
        "quantity": quantity,  # Количество монет
        "price": sell_price,  # Заданная цена
        "stopPrice": stop_price,  # Цена, при которой выставляется лимитная заявка на продажу по стопу
        "stopLimitPrice": stop_limit,  # Цена, по которой продается монета по стопу
        "stopLimitTimeInForce": "GTC",
        "recvWindow": RECVWINDOW,  # Необходимо для предотвращения ошибки 1021
    }
    print(params)
    response = client.new_oco_order(**params)  # Открывает ордер на продажу со стопом
    print(f'respone в sell_coin: {response}')
    stop_order_id = str((response['orders'][0]['orderId']))
    limit_order_id = str((response['orders'][1]['orderId']))
    stop_order_info = client.get_order(symbol="BTCTUSD", orderId=stop_order_id, recvWindow=RECVWINDOW)
    limit_order_info = client.get_order(symbol="BTCTUSD", orderId=limit_order_id, recvWindow=RECVWINDOW)
    stop_order_status = stop_order_info['status']
    limit_order_status = limit_order_info['status']
    print(f'stop_order_info:{stop_order_info}')
    print(f'limit_order_info:{limit_order_info}')
    while stop_order_status != 'FILLED' and limit_order_status != 'FILLED':
        timer = get_timer(logger, version, param='CHECK_T')
        time.sleep(timer)
        stop_order_info = client.get_order("BTCTUSD", orderId=stop_order_id, recvWindow=RECVWINDOW)
        limit_order_info = client.get_order("BTCTUSD", orderId=limit_order_id, recvWindow=RECVWINDOW)
        stop_order_status = stop_order_info['status']
        limit_order_status = limit_order_info['status']
        message = (f'{version}: Проверено состояние ордеров:'
                   f'{stop_order_info}, status: {stop_order_status},'
                   f'{limit_order_info}, status: {limit_order_status},')
        logger.debug(message)
        print(f'statuses:{stop_order_status, limit_order_status}')
    if stop_order_status == 'FILLED':
        order_info = stop_order_info
        message = f'{version}: Продано по стопу'
        logger.info(message)
        send_message(logger, message)
        timer = get_timer(logger, version, param='STOP')
        time.sleep(timer)
    elif limit_order_status == 'FILLED':
        order_info = limit_order_info
        logger.debug(f'{version}: Продано без стопа')
    else:
        order_info = response
        message = f'{version}: Непонятная ошибка со статусами ордеров'
        print(message)
        logger.info(message)
        send_message(logger, message)
        timer = get_timer(logger, version, param='STOP')
        time.sleep(timer)
    print(f'order_info в конце sell_coin: {order_info}')
    message = (f'{version}: Продано {quantity} BTC на сумму '
               f'{order_info["cummulativeQuoteQty"]} TUSD по цене {order_info["price"]}')
    logger.info(message)
    send_message(logger, message)
    return order_info


def get_balance(logger, version, tiker):
    """Показывает количество запрошенной монеты на аккаунте."""
    logger.debug(f'{version}: Проверил баланс {tiker}')
    all_tokens = client.account()["balances"]
    for token in all_tokens:
        if token['asset'] == tiker:
            return float(token['free'])
    return 0


def get_timer(logger, version, param):
    """Определяет время следующего запроса к API в зависимости от исхода."""
    logger.debug(f'{version}: Определил время следующего запроса')
    if param == 'STOP':
        return 150 * 60
    elif param == 'SEARCH':
        return 30
    return COEF[version]['CHECK_T']
