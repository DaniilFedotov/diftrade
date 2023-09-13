import os

from dotenv import load_dotenv
from binance.spot import Spot


TRADER_NAME = 'kittybot_spot_margin'
TOKEN_NAME = 'BTC'
CURRENCY = 'TUSD'

COEF = {'MARGIN_RATIO': 1,
        'INLET': 2,
        'OUTLET': 1.0005,
        'STOP': 0.985,
        'STOP_LIMIT': 0.9845,
        'CHECK_T': 60}

load_dotenv()  # Загружает секретные ключи

BINANCE_TOKEN_S = os.getenv('BINANCE_TOKEN_S')  # Ключ для S
BINANCE_KEY_S = os.getenv('BINANCE_SECRET_KEY_S')  # Ключ для S

CLIENT_BINANCE_S = Spot(api_key=BINANCE_TOKEN_S, api_secret=BINANCE_KEY_S)  # Регистрируем клиента для API-binance
