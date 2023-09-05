import os

from dotenv import load_dotenv
from telegram import Bot
from binance.spot import Spot


TRADER_NAME = 'kittybot_spot_margin_1'
TOKEN_NAME = 'BTC'
CURRENCY = 'TUSD'

COEF = {'INLET': 2,
        'OUTLET': 1.0005,
        'STOP': 0.985,
        'STOP_LIMIT': 0.9845,
        'CHECK_T': 60}

load_dotenv()  # Загружает секретные ключи

BINANCE_TOKEN_D = os.getenv('BINANCE_TOKEN_D')  # Токен для D
BINANCE_KEY_D = os.getenv('BINANCE_SECRET_KEY_D')  # Ключ для D
BINANCE_TOKEN_S = os.getenv('BINANCE_TOKEN_S')  # Ключ для S
BINANCE_KEY_S = os.getenv('BINANCE_SECRET_KEY_S')  # Ключ для S

TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')  # Токен для управления ботом
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')  # ID чата, в который требуется отправка сообщений

LVL_C = {  # LEVEL COEFFICIENTS, коэф-ты для проверки уровней. Определяют толщину уровня и длину участка
    12: {'hc1': 0.1,  # high_coef снизу от уровня
         'hc2': 0.0,  # high_coef сверху от уровня
         'lc': 0.1,  # low-coef сверху от уровня
         'st': 0,  # start - начало интервала
         'end': 12},  # end - конец интервала
    6: {'hc1': 0.1,
        'hc2': 0.0,
        'lc': 0.1,
        'st': 12,
        'end': 18},
    5: {'hc1': 0.12,
        'hc2': 0.12,
        'lc': 0.1,
        'st': 18,
        'end': 23},
    1: {'hc1': 0.12,
        'hc2': 0.0,
        'lc': 0.06,
        'st': 23,
        'end': 24},
    8: {'hc1': 0.27,  # Для предотвращения перекупленности, было 0.22
        'hc2': 0.0,
        'lc': 0.1,
        'st': 16,
        'end': 24}
}

VLT_C = {  # VOLATILITY COEFFICIENTS, коэф-ты для проверки волатильности.
    8: {'hvc': 0.04,  # high_volatility_coef- коэффициент высокой волатильности. Выражен в долях от цены
        'lvc': 0.0025,  # low_volatility_coef - коэффициент низкой волатильности. Выражен в долях от цены
        'st': 16,  # start - начало интервала
        'end': 24},  # end - конец интервала
    3: {'hvc': 0.015,
        'lvc': 0.0025,
        'st': 21,
        'end': 24},
    2: {'hvc': 0.01,
        'lvc': 0.0025,  # На 5минутных таймфреймах добавить проверку волатильности, иначе в начале часа она недост
        'st': 22,
        'end': 24}
}

RECVWINDOW = 59000

BOT_TG = Bot(token=TELEGRAM_TOKEN)  # Регистрируем Telegram-бота

CLIENT_BINANCE_S = Spot(api_key=BINANCE_TOKEN_S, api_secret=BINANCE_KEY_S)  # Регистрируем клиента для API-binance
CLIENT_BINANCE_D = Spot(api_key=BINANCE_TOKEN_D, api_secret=BINANCE_KEY_D)
