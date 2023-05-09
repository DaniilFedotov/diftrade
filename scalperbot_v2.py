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


load_dotenv()

VERSION = 'Scalper_sdk'

BINANCE_TOKEN = os.getenv('BINANCE_TOKEN_SDK')  # Токен для версии через SDK
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

BASE_URL = 'https://api.binance.com'
ENDPOINT = '/api/v3/'
ENDPOINT_FUNC = 'ticker/price'  # Функция, в данный момент получение цены по тикеру
HEADERS = {"Authorization": f"OAuth {BINANCE_TOKEN}"}

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = logging.StreamHandler(stream=sys.stdout)
file_handler = logging.FileHandler(f"log_{VERSION}.log", mode='a')
formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.addHandler(file_handler)

updater = Updater(token=TELEGRAM_TOKEN)


def main():
    """Основная логика работы бота."""
    deposit_info =
    bot = Bot(token=TELEGRAM_TOKEN)


if __name__ == "__main__":
    main()
