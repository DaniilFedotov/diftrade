import os
from binance.spot import Spot
from dotenv import load_dotenv
import requests


load_dotenv()


BINANCE_TOKEN = os.getenv('BINANCE_TOKEN_SDK')  # Токен для версии через SDK
BINANCE_KEY = os.getenv('BINANCE_SECRET_KEY_SDK')  # Ключ для версии через SDK
BASE_URL = 'https://api.binance.com'
ENDPOINT = '/api/v3/'
ENDPOINT_FUNC = 'ticker/price'  # Функция, в данный момент получение цены по тикеру


client = Spot(api_key=BINANCE_TOKEN, api_secret=BINANCE_KEY)
r = requests.get(f'{BASE_URL}{ENDPOINT}{ENDPOINT_FUNC}?symbol=BTCTUSD')
print(float(r.json()["price"]), float(client.ticker_price('BTCTUSD')["price"]))
