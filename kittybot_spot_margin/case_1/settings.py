import os

from dotenv import load_dotenv
from binance.spot import Spot


TRADER_NAME = 'bot_spot_margin'
TOKEN_NAME = 'BTC'
CURRENCY = 'TUSD'

COEF = {'MARGIN_RATIO': 0.1,  # 1:обычный режим. 1-5:плечо. (0.1 для тестирования)
        'INLET': 2,
        'OUTLET': 1.0005,
        'STOP': 0.985,
        'STOP_LIMIT': 0.9845,
        'CHECK_T': 60}

load_dotenv()  # Загружает секретные ключи

BINANCE_TOKEN_S = os.getenv('BINANCE_TOKEN_SECOND')  # Токен для API-binance
BINANCE_KEY_S = os.getenv('BINANCE_SECRET_KEY_SECOND')  # Ключ для API-binance
CLIENT_BINANCE_S = Spot(api_key=BINANCE_TOKEN_S, api_secret=BINANCE_KEY_S)  # Регистрация клиента для API-binance
