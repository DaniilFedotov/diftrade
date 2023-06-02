import datetime
import os
import sys
import time
from random import randint

import logging
import requests

from functions import (VERSIONS, COEF, check_level, check_price, get_logger,
                       buy_coin, sell_coin, get_timer, send_message)


VERSION = VERSIONS[1]  # Выбираем версию бота

logger = get_logger(VERSION)  # Получает логгер


def main():
    """Основная логика работы бота."""
    while True:
        random_factor = randint(1, int(COEF[VERSION]['INLET']))  # Фактор входа для Scalper, основанный на рандоме
        current_price = check_price(logger, VERSION)  # Проверяет текущую цену для проверки уровней
        level_factor = check_level(logger, VERSION, current_price)  # Фактор входа, основанный на уровнях
        logging.debug(f'random_factor: {random_factor}, level_factor: {level_factor}')
        if random_factor == int(COEF[VERSION]['INLET']) and level_factor:  # Если оба фактора указывают на вход в сделку
            buy_info = buy_coin(logger, VERSION)
            sell_info = None
            logging.debug(f'buy_info: {buy_info}')
            if buy_info['status'] == 'FILLED':
                sell_info = sell_coin(logger, VERSION, buy_info)
                logging.debug(f'sell_info: {sell_info}')
            profit = float(sell_info['cummulativeQuoteQty']) - float(buy_info['cummulativeQuoteQty'])
            message = (f'{VERSION}: Сделка закрыта, заработок: '
                       f'{profit} TUSD '
                       f'Текущий депозит (ориентировочно): {sell_info["cummulativeQuoteQty"]} TUSD')
            logging.info(message)
            send_message(logger, message)
        timer = get_timer(logger, VERSION, param='SEARCH')
        time.sleep(timer)


if __name__ == "__main__":
    main()
