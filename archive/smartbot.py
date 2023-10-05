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
TRADER_VERSION = VERSIONS[2] # Выбрать версию бота
BINANCE_TOKEN = os.getenv('BINANCE_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

TIME_STEP_CHECK = 1 # Выбрать частоту проверки в состоянии сделки
TIME_STEP_TGBOT = 20 # Выбрать частоту проверки в состоянии ожидания сделки
TEST_DEPO = {
    'USDT_DEPO': 100.0,
    'BTC_DEPO': 0.0,
}
BASE_URL = 'https://api.binance.com'
ENDPOINT = '/api/v3/'
ENDPOINT_FUNC = 'ticker/price'
HEADERS = {"Authorization": f"OAuth {BINANCE_TOKEN}"}

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler(stream=sys.stdout)
file_handler = logging.FileHandler(f"log_{TRADER_VERSION}.log", mode='a')
formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.addHandler(file_handler)

updater = Updater(token=TELEGRAM_TOKEN)


def sleep(update, context):
    chat = update.effective_chat
    context.bot.send_message(chat_id=chat.id,
                             text=f'Бот {TRADER_VERSION} деактивирован.')
    sys.exit()


def check_deposit_account():
    logger.debug(f'{TRADER_VERSION}: Получен состав кошелька')
    return TEST_DEPO


def check_price():
    r = requests.get(f'{BASE_URL}{ENDPOINT}{ENDPOINT_FUNC}?symbol=BTCUSDT')
    logger.debug(f'{TRADER_VERSION}: Цена проверена: '
                 f'{float(r.json()["price"])} USDT')
    return float(r.json()["price"])


def hash(hash_list, current_price):
    new_hash_list = []
    for i in range(1, 5):
        new_hash_list.append(hash_list[i])
    new_hash_list.append(current_price)
    return new_hash_list


def buy_coin(deposit_info, current_price):
    quantity = deposit_info['USDT_DEPO'] / current_price
    dt = datetime.datetime.now()
    logger.debug(f'{TRADER_VERSION}: Куплено {quantity} BTC на сумму '
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
    quantity = deal_info['quantity']
    dt = datetime.datetime.now()
    profit = (quantity * current_price -
              deal_info['quantity'] * deal_info['purchase_price'])
    logger.debug(f'{TRADER_VERSION}: Продано {quantity} BTC на сумму '
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
    hash_list = [0, 0, 0, 0, 0]
    deposit_info = check_deposit_account()
    while True:
        current_price = check_price()
        hash_list = hash(hash_list, current_price)
        if current_price <= max(hash_list) * 0.9995:
            deal_info, deposit_info = buy_coin(deposit_info, current_price)
            while deal_info['in_deal']:
                current_price = check_price()
                if current_price >= deal_info['purchase_price'] * 1.0002:
                    deal_info, deposit_info = sell_coin(
                        deposit_info,
                        current_price,
                        deal_info)
                time.sleep(TIME_STEP_CHECK)
            message = (f'{TRADER_VERSION}: Сделка закрыта, заработок: '
                       f'{deal_info["profit"]} USDT '
                       f'Текущий депозит: {deposit_info["USDT_DEPO"]} USDT')
            logger.debug(message)
            send_message(bot, message)
            hash_list = [0, 0, 0, 0, deal_info['selling_price']]
        time.sleep(TIME_STEP_TGBOT)


if __name__ == "__main__":
    main()
