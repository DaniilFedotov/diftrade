import os

from dotenv import load_dotenv
from telegram import Bot


load_dotenv()  # Загружает секретные ключи

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
        'lvc': 0.0025,  # На 5-минутных ТФ добавить проверку ВОЛ
        'st': 22,
        'end': 24}
}

# То, на сколько уменьшается цена покупки для выполнения ордера в режиме MAKER
PRICE_DELTA_BTC = 0.5

# Время жизни лимитного ордера на покупку в милисекундах
BUY_ORDER_LIFETIME = 120000

# Промежуток в милисекундах для отслеживания комиссии
TIMEDELTA_COMMISSION = 36000000

# Время сна в секундах в случае ненулевой комиссии
SLEEPTIME_COMMISSION = 360000

RECVWINDOW = 59000

# Регистрация Telegram-бота
BOT_TG = Bot(token=TELEGRAM_TOKEN)
