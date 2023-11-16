import os

from dotenv import load_dotenv
from telegram import Bot
from binance.spot import Spot


TRADER_NAME = 'bot_spot'
TOKEN_NAME = 'BTC'
CURRENCY = 'TUSD'

COEF = {'INLET': 2,
        'OUTLET': 1.0005,
        'STOP': 0.985,
        'STOP_LIMIT': 0.9845,
        'CHECK_T': 60}

load_dotenv()  # Загружает секретные ключи

# Токен для API-binance
BINANCE_TOKEN_F = os.getenv('BINANCE_TOKEN_FIRST')
# Ключ для API-binance
BINANCE_KEY_F = os.getenv('BINANCE_SECRET_KEY_FIRST')
# Токен для для API-binance
BINANCE_TOKEN_S = os.getenv('BINANCE_TOKEN_SECOND')
# Ключ для API-binance
BINANCE_KEY_S = os.getenv('BINANCE_SECRET_KEY_SECOND')

# Токен для управления ботом
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
# ID чата, в который требуется отправка сообщений
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

# LEVEL COEFFICIENTS, коэф-ты для проверки уровней.
# Определяют толщину уровня и длину участка.
LVL_C = {
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

# hvc - high_volatility_coef - коэффициент высокой волатильности.
# lvc - low_volatility_coef - коэффициент низкой волатильности.
# Коэффициенты выражены в долях от цены.
VLT_C = {  # VOLATILITY COEFFICIENTS, коэф-ты для проверки волатильности.
    8: {'hvc': 0.04,
        'lvc': 0.0025,
        'st': 16,  # start - начало интервала
        'end': 24},  # end - конец интервала
    3: {'hvc': 0.015,
        'lvc': 0.0025,
        'st': 21,
        'end': 24},
    2: {'hvc': 0.01,
        'lvc': 0.0025,  # На 5минутных ТФ добавить проверку ВОЛ
        'st': 22,
        'end': 24}
}

RECVWINDOW = 59000

# Регистрируем Telegram-бота
BOT_TG = Bot(token=TELEGRAM_TOKEN)

# Регистрируем клиента для API-binance
CLIENT_BINANCE_S = Spot(api_key=BINANCE_TOKEN_S, api_secret=BINANCE_KEY_S)
CLIENT_BINANCE_F = Spot(api_key=BINANCE_TOKEN_F, api_secret=BINANCE_KEY_F)
