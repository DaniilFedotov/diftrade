import os
import sys

import logging
import requests
from dotenv import load_dotenv
from telegram import TelegramError, Bot
from binance.spot import Spot


VERSIONS = ['Trader_sdk', 'Scalper_sdk', 'Smart_sdk']
COEF = {VERSIONS[0]: {'INLET': 0.9992,
                      'OUTLET': 1.0008,
                      'STOP': 0.98},
        VERSIONS[1]: {'INLET': 5,
                      'OUTLET': 1.0004,
                      'STOP': 0.985},
        VERSIONS[2]: {'INLET': 0.9990,
                      'OUTLET': 1.0025,
                      'STOP': 0.98}}

load_dotenv()

BINANCE_TOKEN = os.getenv('BINANCE_TOKEN_SDK')  # Токен для версии через SDK
BINANCE_KEY = os.getenv('BINANCE_SECRET_KEY_SDK')  # Ключ для версии через SDK
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

BASE_URL = 'https://api.binance.com'
ENDPOINT = '/api/v3/'
ENDPOINT_FUNC = 'ticker/price'  # Функция, в данный момент получение цены по тикеру
HEADERS = {"Authorization": f"OAuth {BINANCE_TOKEN}"}

DEF = {  # DEFINITION, коэф-ты для проверки уровней
    24: {'hc': 0.2,  # high_coef
         'lc': 0.1},  # low_coef
    12: {'hc': 0.18,
         'lc': 0.09},
    6: {'hc': 0.16,
        'lc': 0.08},
    3: {'hc': 0.14,
        'lc': 0.07},
    1: {'hc': 0.12,
        'lc': 0.06}
}

bot = Bot(token=TELEGRAM_TOKEN)

client = Spot(api_key=BINANCE_TOKEN, api_secret=BINANCE_KEY)


def get_logger(version):
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    handler = logging.StreamHandler(stream=sys.stdout)
    file_handler = logging.FileHandler(f"log_{version}.log", mode='a')
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.addHandler(file_handler)
    return logger


def check_level(logger, version, current_price):
    """Проверяет, находится ли цена в допустимом для входа диапазоне."""
    logger.debug(f'{version}: Проверены уровни для входа')
    intervals = DEF.keys()
    data = client.klines('BTCTUSD', '1h', limit=24)
    for interval in intervals:  # Для каждого из временных промежутков
        highs = []
        lows = []
        for data_hour in data[-interval:]:  # Для каждого часа из временного промежутка
            highs.append(data_hour[2])  # Добавляем наибольшее значение для часа в список
            lows.append(data_hour[3])  # Добавляем наименьшее значение для часа в список
        width = max(highs) - min(lows)  # Находим длину коридора для временного промежутка
        if (max(highs) - DEF[interval]['hc'] * width < current_price or
                current_price < min(lows) + DEF[interval]['lc'] * width):
            return False
    return True


def check_price(logger, version):
    """Проверяет цену монеты."""
    try:
        price = float(client.ticker_price('BTCTUSD')["price"])
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
        bot.send_message(TELEGRAM_CHAT_ID, message)
        logger.debug(f'Сообщение в Telegram отправлено: {message}')
    except TelegramError:
        logger.error(f'Сбой при отправке сообщения в Telegram: {message}')


def buy_coin(logger, version):
    """Выставляет ордер на покупку монеты."""
    params = {
        "symbol": "BTCTUSD",
        "side": "BUY",
        "type": "MARKET",
        "quantity": 1,
    }
    response = client.new_order(**params)  # Открывает ордер на покупку по рыночной цене
    # Для расчета цены продажи и стопа необходимо запросить инфу по исполненому ордеру и подсосать цену покупки
    return response  # Видимо, в респонсе можно достать цену покупки, нужно вернуть для перехода к функции продажи


def sell_coin(logger, version):
    """Выставляет ордер на продажу монеты по заданной цене."""
    params = {
        "symbol": "BTCTUSD",
        "side": "SELL",
        "quantity": 1,
        "price": 1,
        "stopPrice": 1,
        "stopLimitPrice": 1,
    }
    response = client.new_oco_order(**params)  # Открывает ордер на продажу со стопом
    message = (f'{version}: Куплено {quantity} BTC на сумму '
               f'{quantity * current_price} USDT по цене {current_price}')
    logger.info(message)
    send_message(logger, message)
    return response
