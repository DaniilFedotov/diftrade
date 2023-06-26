import os

from dotenv import load_dotenv
from telegram import Bot
from binance.spot import Spot


COEF = {'INLET': 5,
        'OUTLET': 1.0005,
        'STOP': 0.985,
        'STOP_LIMIT': 0.9845,
        'CHECK_T': 60}

load_dotenv()  # Загружает секретные ключи

BINANCE_TOKEN = os.getenv('BINANCE_TOKEN_SDK')  # Токен для версии через SDK
BINANCE_KEY = os.getenv('BINANCE_SECRET_KEY_SDK')  # Ключ для версии через SDK
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
    8: {'hc1': 0.22,  # Для предотвращения перекупленности
        'hc2': 0.0,
        'lc': 0.1,
        'st': 16,
        'end': 24}
}  # Сумма ключей должна быть равна 24 (часам)

RECVWINDOW = 59000

BOT_TG = Bot(token=TELEGRAM_TOKEN)  # Регистрируем Telegram-бота

CLIENT_BINANCE = Spot(api_key=BINANCE_TOKEN, api_secret=BINANCE_KEY)  # Регистрируем клиента для API-binance