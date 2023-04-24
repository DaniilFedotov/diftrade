import datetime
import os
import sys
import time
import logging
import requests
from telegram import Bot, ReplyKeyboardMarkup, TelegramError
from telegram.ext import Updater, CommandHandler
from dotenv import load_dotenv


load_dotenv()


VERSIONS = ['Trader', 'Scalper', 'Smart']
VERSION = VERSIONS[0] # Выбрать версию бота
COEF = {VERSIONS[0]: {'SEARCH_TIME': 20,
                      'CHECK_TIME': 6,
                      'SLOW_CHECK_TIME': 60,
                      'INLET': 0.9995,
                      'OUTLET': 1.0005,
                      'STOP': 0.98,
                      },
        VERSIONS[1]: {'SEARCH_TIME': 15,
                      'CHECK_TIME': 3,
                      'SLOW_CHECK_TIME': 30,
                      'INLET': 5,
                      'OUTLET': 1.0002,
                      'STOP': 0.985,
                      },
        VERSIONS[2]: {'SEARCH_TIME': 15,
                      'CHECK_TIME': 3,
                      'SLOW_CHECK_TIME': 30,
                      'INLET': 0.9995,
                      'OUTLET': 1.0003,
                      'STOP': 0.985,
                      },
        }
TEST_DEPO = {
    'USDT_DEPO': 100.0,
    'BTC_DEPO': 0.0,
}

BINANCE_TOKEN = os.getenv('BINANCE_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

BASE_URL = 'https://api.binance.com'
ENDPOINT = '/api/v3/'
ENDPOINT_FUNC = 'ticker/price'
HEADERS = {"Authorization": f"OAuth {BINANCE_TOKEN}"}

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler(stream=sys.stdout)
file_handler = logging.FileHandler(f"log_{VERSION}.log", mode='a')
formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.addHandler(file_handler)

updater = Updater(token=TELEGRAM_TOKEN)


def sleep(update, context):
    """Отправляет бота в спячку."""
    chat = update.effective_chat
    context.bot.send_message(chat_id=chat.id,
                             text=f'Мяу! Пока! {VERSION} ушел.')
    sys.exit()


def check_deposit_account():
    """Проверяет активы на кошельке."""
    logger.debug(f'{VERSION}: Получен состав кошелька')
    return TEST_DEPO


def check_price():
    """Проверяет цену монеты."""
    r = requests.get(f'{BASE_URL}{ENDPOINT}{ENDPOINT_FUNC}?symbol=BTCUSDT')
    logger.debug(f'{VERSION}: Цена проверена: '
                 f'{float(r.json()["price"])} USDT')
    return float(r.json()["price"])


def check_level(cache_list, current_price):
    """Проверяет, находится ли цена в допустимом для входа диапазоне."""
    width = max(cache_list) - min(cache_list)
    if min(cache_list) + 0.1 * width < current_price < max(cache_list) - 0.3 * width:
        return True
    return False


def get_timer(current_price, purchase_price):
    """Определяет время следующего запроса к API в зависимости
     от положения текущей цены относительно цены покупки.
     """
    if abs(purchase_price - current_price) >= current_price * 0.003:
        return COEF[VERSION]['SLOW_CHECK_TIME']
    return COEF[VERSION]['CHECK_TIME']


def setup_cache(cache_level):
    """Производит заполнение кэша для создания первоначальных уровней."""
    while len(cache_level) < 5 * 60 / COEF[VERSION]['SEARCH_TIME']:
        current_price = check_price()
        cache_level = cache(cache_level, current_price, 120 * 60 / COEF[VERSION]['CHECK_TIME'])
        time.sleep(COEF[VERSION]['SEARCH_TIME'])
    return cache_level


def cache(cache_list, current_price, size):
    """Создает кэш, размер которого задан параметром size,
    определяемым длиной кэшируемого участка на временном графике.
    """
    if len(cache_list) == int(size):
        new_cache_list = []
        for i in range(1, int(size)):
            new_cache_list.append(cache_list[i])
        new_cache_list.append(current_price)
        return new_cache_list
    cache_list.append(current_price)
    return cache_list


def buy_coin(deposit_info, current_price):
    """Приобретает монеты по заданной цене."""
    quantity = deposit_info['USDT_DEPO'] / current_price
    dt = datetime.datetime.now()
    logger.debug(f'{VERSION}: Куплено {quantity} BTC на сумму '
                 f'{quantity * current_price} USDT по цене {current_price}')
    deal_info = {
        'in_deal': True,
        'purchase_price': current_price,
        'quantity': quantity,
        'date_of_purchase': dt
    }
    deposit_info['USDT_DEPO'] -= quantity * current_price
    deposit_info['BTC_DEPO'] += quantity
    return deal_info, deposit_info


def sell_coin(deposit_info, current_price, deal_info):
    """Продает монеты по заданной цене."""
    quantity = deal_info['quantity']
    dt = datetime.datetime.now()
    profit = (quantity * current_price -
              deal_info['quantity'] * deal_info['purchase_price'])
    logger.debug(f'{VERSION}: Продано {quantity} BTC на сумму '
                 f'{quantity * current_price} USDT по цене {current_price}')
    deal_info = {
        'in_deal': False,
        'selling_price': current_price,
        'quantity': quantity,
        'date_of_purchase': dt,
        'profit': profit,
    }
    deposit_info['USDT_DEPO'] += quantity * current_price
    deposit_info['BTC_DEPO'] -= quantity
    return deal_info, deposit_info


def send_message(bot, message):
    """Отправляет сообщение в Telegram чат."""
    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)
        logger.debug(f'Сообщение в Telegram отправлено: {message}')
    except TelegramError:
        logger.error(f'Сбой при отправке сообщения в Telegram: {message}')


def main():
    """Основная логика работы бота."""
    bot = Bot(token=TELEGRAM_TOKEN)
    cache_inlet = setup_cache([])
    cache_level = setup_cache([])
    deposit_info = check_deposit_account()
    while True:
        current_price = check_price()
        cache_inlet = cache(cache_inlet, current_price, 5 * 60 / COEF[VERSION]['SEARCH_TIME'])
        cache_level = cache(cache_level, current_price, 120 * 60 / COEF[VERSION]['CHECK_TIME'])
        level_factor = check_level(cache_level, current_price)
        if current_price <= max(cache_inlet) * COEF[VERSION]['INLET'] and level_factor:
            deal_info, deposit_info = buy_coin(deposit_info, current_price)
            while deal_info['in_deal']:
                current_price = check_price()
                cache_level = cache(cache_level, current_price, 120 * 60 / COEF[VERSION]['CHECK_TIME'])
                if current_price < deal_info['purchase_price'] * COEF[VERSION]['STOP']:
                    deal_info, deposit_info = sell_coin(
                        deposit_info,
                        current_price,
                        deal_info)
                    message = f'{VERSION}: Вылетел по стопу'
                    logger.debug(message)
                    send_message(bot, message)
                elif current_price >= deal_info['purchase_price'] * COEF[VERSION]['OUTLET']:
                    deal_info, deposit_info = sell_coin(
                        deposit_info,
                        current_price,
                        deal_info)
                else:
                    timer = get_timer(current_price, deal_info['purchase_price'])
                    time.sleep(timer)
            message = (f'{VERSION}: Сделка закрыта, зароботок: '
                       f'{deal_info["profit"]} USDT '
                       f'Текущий депозит: {deposit_info["USDT_DEPO"]} USDT')
            logger.debug(message)
            send_message(bot, message)
            cache_inlet = cache_level
        time.sleep(COEF[VERSION]['SEARCH_TIME'])


if __name__ == "__main__":
    main()
