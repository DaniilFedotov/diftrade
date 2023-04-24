import datetime
import os
import sys
import time
from random import randint
import logging
import requests
from telegram import Bot, ReplyKeyboardMarkup, TelegramError
from telegram.ext import Updater, CommandHandler
from dotenv import load_dotenv
from traderbot import (sleep, check_deposit_account, check_price, check_level, get_timer,
                       setup_cache, cache, buy_coin, sell_coin, send_message, COEF)


load_dotenv()


VERSIONS = ['Trader', 'Scalper', 'Smart']
VERSION = VERSIONS[1] # Выбрать версию бота

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


def main():
    """Основная логика работы бота."""
    bot = Bot(token=TELEGRAM_TOKEN)
    cache_level = setup_cache([])
    deposit_info = check_deposit_account()
    while True:
        current_price = check_price()
        random_inlet = randint(1, int(COEF[VERSION]['INLET']))
        cache_level = cache(cache_level, current_price, 120 * 60 / COEF[VERSION]['CHECK_TIME'])
        level_factor = check_level(cache_level, current_price)
        if random_inlet == int(COEF[VERSION]['INLET']) and level_factor:
            deal_info, deposit_info = buy_coin(deposit_info, current_price)
            while deal_info['in_deal']:
                current_price = check_price()
                cache_level = cache(cache_level, current_price, 120 * 60 / COEF[VERSION]['CHECK_TIME'])
                if current_price <= deal_info['purchase_price'] * COEF[VERSION]['STOP']:
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
        time.sleep(COEF[VERSION]['SEARCH_TIME'])


if __name__ == "__main__":
    main()
