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
from binance.spot import Spot

from functions import (VERSIONS, COEF, BINANCE_TOKEN, BINANCE_KEY, TELEGRAM_TOKEN,
                       TELEGRAM_CHAT_ID, check_level, check_price, get_logger,
                       buy_coin, sell_coin)


load_dotenv()

VERSION = VERSIONS[1]

logger = get_logger(VERSION)


def main():
    """Основная логика работы бота."""
    while True:
        random_factor = randint(1, int(COEF[VERSION]['INLET']))
        current_price = check_price(logger, VERSION)
        level_factor = check_level(logger, VERSION, current_price)
        if random_factor == int(COEF[VERSION]['INLET']) and level_factor:
            print(random_factor, level_factor)  # Затестить работу check_level
            trade_info = buy_coin(logger, VERSION)  # Затестить ордера через лимитки или тестнет
            while True:
                check_order()



if __name__ == "__main__":
    main()
