from random import randint
import time

from telegram import TelegramError

from constants import COEF, LVL_C, VLT_C, BOT_TG, RECVWINDOW, TELEGRAM_CHAT_ID


class Trader:  # Родительский класс для торговых ботов
    def __init__(self, name, logger, token, currency, client):
        self.name = name
        self.logger = logger
        self.token = token
        self.currency = currency
        self.pair = token + currency
        self.client = client

    def check_price(self):
        """Проверяет цену монеты."""
        try:
            price = float(self.client.ticker_price(self.pair)["price"])  # Получает цену токена
            self.logger.debug(f'{self.name}: Цена проверена: {price} {self.currency}')
            return price
        except Exception as error:
            message = f'Ошибка при проверке цены: {error}'
            self.logger.error(message)
            self.send_message(message)
            raise Exception(message)

    def send_message(self, message):
        """Отправляет сообщение в Telegram чат."""
        try:
            BOT_TG.send_message(TELEGRAM_CHAT_ID, message)  # Бот отправляет сообщение в телеграм по указанному ID
            self.logger.debug(f'Сообщение в Telegram отправлено: {message}')
        except TelegramError:
            self.logger.error(f'Сбой при отправке сообщения в Telegram: {message}')

    def get_timer(self, param):
        """Определяет время следующего запроса к API в зависимости от исхода."""
        self.logger.debug(f'{self.name}: Определил время следующего запроса')
        if param == 'STOP':
            return 150 * 60
        elif param == 'SEARCH':
            return 30
        return COEF['CHECK_T']


class TraderSpotMargin(Trader):  # Класс для спотовой торговли
    def get_balance(self):
        """Показывает количество запрошенной монеты на аккаунте."""
        self.logger.debug(f'{self.name}: Проверил баланс {self.currency}')
        all_tokens = self.client.account()["balances"]
        for token in all_tokens:
            if token['asset'] == self.currency:  # Для указанного тикера
                return float(token['free'])
        return 0

    def check_inlet_condition(self):
        """Проверяет условие для входа, зависящее от версии бота."""
        random_factor = randint(1, int(COEF['INLET']))  # Фактор входа, основанный на рандоме
        return random_factor == int(COEF['INLET'])  # True/False

    def buy_coin(self, cur_depo, cur_price):
        """Выставляет рыночный ордер на покупку монеты."""
        try:
            quote = self.get_balance()
        except Exception:
            quote = cur_depo
            message = f'{self.name}: Баланс принят равным: {cur_depo} {self.currency}(Искл)'
            self.logger.error(message)
            self.send_message(message)


    def sell_coin(self, buy_info):
        """Выставляет ОСО ордер на продажу монеты по заданной цене."""


    def check_level(self, cur_price):
        """Проверяет, находится ли цена в допустимом для входа диапазоне."""
        data_24h = self.client.klines(self.pair, '1h', limit=24)  # В ответ на API-запрос получает свечи за период
        # data_60m = self.client.klines(self.pair, '5m', limit=12)  # В ответ на API-запрос получает свечи за период
        checks_box = []
        check_first = self.check_global_level(cur_price, data_24h)  # True/False
        checks_box.append(check_first)
        check_second = self.check_admissible_volatility(cur_price, data_24h)  # True/False
        checks_box.append(check_second)
        # check_third = self.check_small_timeframe(cur_price, data_60m)  # True/False
        # checks_box.append(check_third)

        for check in checks_box:
            if not check:  # Если одна из проверок показала отрицательный результат
                self.logger.debug(f'{self.name}: Глобальная проверка: False')
                return False  # Вход в сделку не допускается
        self.logger.debug(f'{self.name}: Глобальная проверка: True')
        return True  # Вход в сделку допускается

    def check_global_level(self, cur_price, data_24h):
        """Проверяет, находится ли текущая цена в пределах глобальных уровней."""
        intervals = LVL_C.keys()  # Содержит в себе нелинейные временные промежутки на таймфрейме
        for dt in intervals:  # Для каждого из временных промежутков
            highs = []
            lows = []
            for data_hour in data_24h[LVL_C[dt]['st']:LVL_C[dt]['end']]:  # Для каждого часа из промежутка
                highs.append(float(data_hour[2]))  # Добавляем наибольшее значение цены для часа в список
                lows.append(float(data_hour[3]))  # Добавляем наименьшее значение цены для часа в список
            width = max(highs) - min(lows)  # Находим длину коридора для временного промежутка
            if (max(highs) - LVL_C[dt]['hc1'] * width < cur_price < max(highs) + LVL_C[dt]['hc2'] * width or
                    min(lows) < cur_price < min(lows) + LVL_C[dt]['lc'] * width):  # Если цена в промежутке
                self.logger.debug(f'{self.name}: Проверены уровни для входа: False. '
                                  f'Проверку уровней не прошел промежуток: {dt}')
                return False  # Если цена находится в пределах толщины одного из уровней
        self.logger.debug(f'{self.name}: Проверены уровни для входа: True')
        return True  # Если цена не находится в пределах толщины одного из уровней

    def check_admissible_volatility(self, cur_price, data_24h):
        """Проверяет, находится ли текущая волатильность в пределах допустимой величины."""
        intervals = VLT_C.keys()  # Содержит в себе нелинейные временные промежутки на таймфрейме
        for dt in intervals:  # Для каждого из временных промежутков
            highs = []
            lows = []
            for data_hour in data_24h[VLT_C[dt]['st']:VLT_C[dt]['end']]:  # Для каждого часа из промежутка
                highs.append(float(data_hour[2]))  # Добавляем наибольшее значение цены для часа в список
                lows.append(float(data_hour[3]))  # Добавляем наименьшее значение цены для часа в список
            width = max(highs) - min(lows)  # Находим длину коридора для временного промежутка
            if width < VLT_C[dt]['lvc'] * cur_price or width > VLT_C[dt]['hvc'] * cur_price:
                self.logger.debug(f'{self.name}: Проверена волатильность: False. '
                                  f'Проверку волатильности не прошел промежуток: {dt}')
                return False  # Если волатильность не находится в пределах допустимой величины
        self.logger.debug(f'{self.name}: Проверена волатильность: True')
        return True  # Если волатильность находится в пределах допустимой величины

    def check_small_timeframe(self, cur_price, data_60m):
        """Проверяет, не находится ли текущая цена в зоне перекупленности на малом таймфрейме."""
        return True