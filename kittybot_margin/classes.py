from random import randint
import time

from telegram import TelegramError

from constants import COEF, LVL_C, VLT_C, CLIENT_BINANCE, CLIENT_BINANCE_OLD, BOT_TG, RECVWINDOW, TELEGRAM_CHAT_ID


class Trader:  # Родительский класс для торговых ботов
    def __init__(self, name, logger):
        self.name = name
        self.logger = logger

    def check_inlet_condition(self):
        """Проверяет условие для входа, зависящее от версии бота."""
        random_factor = randint(1, int(COEF['INLET']))  # Фактор входа, основанный на рандоме
        return random_factor == int(COEF['INLET'])  # True/False

    def check_price(self):
        """Проверяет цену монеты."""
        try:
            price = float(CLIENT_BINANCE.ticker_price('BTCTUSD')["price"])  # В ответ на API-запрос получает цену монеты
            self.logger.debug(f'{self.name}: Цена проверена: {price} TUSD')
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

    def get_balance(self, tiker):
        """Показывает количество запрошенной монеты на аккаунте."""
        self.logger.debug(f'{self.name}: Проверил баланс {tiker}')
        all_tokens = CLIENT_BINANCE.account()["balances"]
        for token in all_tokens:
            if token['asset'] == tiker:  # Для указанного тикера
                return float(token['free'])
        return 0

    def get_timer(self, param):
        """Определяет время следующего запроса к API в зависимости от исхода."""
        self.logger.debug(f'{self.name}: Определил время следующего запроса')
        if param == 'STOP':
            return 150 * 60
        elif param == 'SEARCH':
            return 30
        return COEF['CHECK_T']


class TraderSpot(Trader):  # Класс для спотовой торговли
    def buy_coin(self, cur_depo):
        """Выставляет рыночный ордер на покупку монеты."""
        try:
            quote = self.get_balance('TUSD')
        except Exception:
            quote = cur_depo
            message = f'{self.name}: Баланс принят равным: {cur_depo} (Искл)'
            self.logger.error(message)
            self.send_message(message)
        params = {
            "symbol": "BTCTUSD",  # Тикер токена
            "side": "BUY",  # Покупка
            "type": "MARKET",  # Тип ордера - рыночный
            "quoteOrderQty": quote,  # Сумма TUSD на ордер
        }
        response = CLIENT_BINANCE.new_order(**params)  # Открывает ордер на покупку по рыночной цене
        message = (f'{self.name}: Куплено {response["origQty"]} BTC на сумму '
                   f'{response["cummulativeQuoteQty"]} TUSD по цене {response["fills"][0]["price"]}')
        self.logger.info(message)
        self.send_message(message)
        return response

    def sell_coin(self, buy_info):
        """Выставляет ОСО ордер на продажу монеты по заданной цене."""
        quantity = float(buy_info['origQty'])
        price = float(buy_info['cummulativeQuoteQty']) / quantity
        sell_price = int(price * COEF['OUTLET'])
        stop_price = int(price * COEF['STOP'])
        stop_limit = int(price * COEF['STOP_LIMIT'])
        params = {
            "symbol": "BTCTUSD",  # Тикер токена
            "side": "SELL",  # Продажа
            "quantity": quantity,  # Количество монет
            "price": sell_price,  # Заданная цена
            "stopPrice": stop_price,  # Цена, при которой выставляется лимитная заявка на продажу по стопу
            "stopLimitPrice": stop_limit,  # Цена, по которой продается монета по стопу
            "stopLimitTimeInForce": "GTC",
            "recvWindow": RECVWINDOW,  # Необходимо для предотвращения ошибки 1021
        }
        response = CLIENT_BINANCE.new_oco_order(**params)  # Открывает ордер на продажу со стопом
        stop_order_id = str((response['orders'][0]['orderId']))
        limit_order_id = str((response['orders'][1]['orderId']))
        stop_order_info = CLIENT_BINANCE.get_order(symbol="BTCTUSD", orderId=stop_order_id, recvWindow=RECVWINDOW)
        limit_order_info = CLIENT_BINANCE.get_order(symbol="BTCTUSD", orderId=limit_order_id, recvWindow=RECVWINDOW)
        stop_order_status = stop_order_info['status']
        limit_order_status = limit_order_info['status']
        while stop_order_status != 'FILLED' and limit_order_status != 'FILLED':
            timer = self.get_timer(param='CHECK_T')
            time.sleep(timer)
            stop_order_info = CLIENT_BINANCE.get_order("BTCTUSD", orderId=stop_order_id, recvWindow=RECVWINDOW)
            limit_order_info = CLIENT_BINANCE.get_order("BTCTUSD", orderId=limit_order_id, recvWindow=RECVWINDOW)
            stop_order_status = stop_order_info['status']
            limit_order_status = limit_order_info['status']
            message = (f'{self.name}: Проверено состояние ордеров:'
                       f'{stop_order_info}, status: {stop_order_status},'
                       f'{limit_order_info}, status: {limit_order_status},')
            self.logger.debug(message)
        if stop_order_status == 'FILLED':
            order_info = stop_order_info
            message = f'{self.name}: Продано по стопу'
            self.logger.info(message)
            self.send_message(message)
            timer = self.get_timer(param='STOP')
            time.sleep(timer)
        elif limit_order_status == 'FILLED':
            order_info = limit_order_info
            self.logger.debug(f'{self.name}: Продано без стопа')
        else:
            order_info = response
            message = f'{self.name}: Непонятная ошибка со статусами ордеров'
            self.logger.info(message)
            self.send_message(message)
            timer = self.get_timer(param='STOP')
            time.sleep(timer)
        message = (f'{self.name}: Продано {quantity} BTC на сумму '
                   f'{order_info["cummulativeQuoteQty"]} TUSD по цене {order_info["price"]}')
        self.logger.info(message)
        self.send_message(message)
        return order_info

    def check_level(self, cur_price):
        """Проверяет, находится ли цена в допустимом для входа диапазоне."""
        data_24h = CLIENT_BINANCE.klines('BTCTUSD', '1h', limit=24)  # В ответ на API-запрос получает свечи за период
        #data_60m = CLIENT_BINANCE.klines('BTCTUSD', '5m', limit=12)  # В ответ на API-запрос получает свечи за период
        checks_box = []
        check_first = self.check_global_level(cur_price, data_24h)  # True/False
        checks_box.append(check_first)
        check_second = self.check_admissible_volatility(cur_price, data_24h)  # True/False
        checks_box.append(check_second)
        #check_third = self.check_small_timeframe(cur_price, data_60m)  # True/False
        #checks_box.append(check_third)

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
                self.logger.debug(f'{self.name}: Проверены уровни для входа: False')
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
                self.logger.debug(f'{self.name}: Проверена волатильность: False')
                return False  # Если волатильность не находится в пределах допустимой величины
        self.logger.debug(f'{self.name}: Проверена волатильность: True')
        return True  # Если волатильность находится в пределах допустимой величины

    def check_small_timeframe(self, cur_price, data_60m):
        """Проверяет, не находится ли текущая цена в зоне перекупленности на малом таймфрейме."""
        return True


class TraderSpotOld(Trader):  # Класс для спотовой торговли
    def buy_coin(self, cur_depo):
        """Выставляет рыночный ордер на покупку монеты."""
        try:
            quote = self.get_balance('TUSD')
        except Exception:
            quote = cur_depo
            message = f'{self.name}: Баланс принят равным: {cur_depo} (Искл)'
            self.logger.error(message)
            self.send_message(message)
        params = {
            "symbol": "BTCTUSD",  # Тикер токена
            "side": "BUY",  # Покупка
            "type": "MARKET",  # Тип ордера - рыночный
            "quoteOrderQty": quote,  # Сумма TUSD на ордер
        }
        response = CLIENT_BINANCE_OLD.new_order(**params)  # Открывает ордер на покупку по рыночной цене
        message = (f'{self.name}: Куплено {response["origQty"]} BTC на сумму '
                   f'{response["cummulativeQuoteQty"]} TUSD по цене {response["fills"][0]["price"]}')
        self.logger.info(message)
        self.send_message(message)
        return response

    def sell_coin(self, buy_info):
        """Выставляет ОСО ордер на продажу монеты по заданной цене."""
        quantity = float(buy_info['origQty'])
        price = float(buy_info['cummulativeQuoteQty']) / quantity
        sell_price = int(price * COEF['OUTLET'])
        stop_price = int(price * COEF['STOP'])
        stop_limit = int(price * COEF['STOP_LIMIT'])
        params = {
            "symbol": "BTCTUSD",  # Тикер токена
            "side": "SELL",  # Продажа
            "quantity": quantity,  # Количество монет
            "price": sell_price,  # Заданная цена
            "stopPrice": stop_price,  # Цена, при которой выставляется лимитная заявка на продажу по стопу
            "stopLimitPrice": stop_limit,  # Цена, по которой продается монета по стопу
            "stopLimitTimeInForce": "GTC",
            "recvWindow": RECVWINDOW,  # Необходимо для предотвращения ошибки 1021
        }
        response = CLIENT_BINANCE_OLD.new_oco_order(**params)  # Открывает ордер на продажу со стопом
        stop_order_id = str((response['orders'][0]['orderId']))
        limit_order_id = str((response['orders'][1]['orderId']))
        stop_order_info = CLIENT_BINANCE_OLD.get_order(symbol="BTCTUSD", orderId=stop_order_id, recvWindow=RECVWINDOW)
        limit_order_info = CLIENT_BINANCE_OLD.get_order(symbol="BTCTUSD", orderId=limit_order_id, recvWindow=RECVWINDOW)
        stop_order_status = stop_order_info['status']
        limit_order_status = limit_order_info['status']
        while stop_order_status != 'FILLED' and limit_order_status != 'FILLED':
            timer = self.get_timer(param='CHECK_T')
            time.sleep(timer)
            stop_order_info = CLIENT_BINANCE_OLD.get_order("BTCTUSD", orderId=stop_order_id, recvWindow=RECVWINDOW)
            limit_order_info = CLIENT_BINANCE_OLD.get_order("BTCTUSD", orderId=limit_order_id, recvWindow=RECVWINDOW)
            stop_order_status = stop_order_info['status']
            limit_order_status = limit_order_info['status']
            message = (f'{self.name}: Проверено состояние ордеров:'
                       f'{stop_order_info}, status: {stop_order_status},'
                       f'{limit_order_info}, status: {limit_order_status},')
            self.logger.debug(message)
        if stop_order_status == 'FILLED':
            order_info = stop_order_info
            message = f'{self.name}: Продано по стопу'
            self.logger.info(message)
            self.send_message(message)
            timer = self.get_timer(param='STOP')
            time.sleep(timer)
        elif limit_order_status == 'FILLED':
            order_info = limit_order_info
            self.logger.debug(f'{self.name}: Продано без стопа')
        else:
            order_info = response
            message = f'{self.name}: Непонятная ошибка со статусами ордеров'
            self.logger.info(message)
            self.send_message(message)
            timer = self.get_timer(param='STOP')
            time.sleep(timer)
        message = (f'{self.name}: Продано {quantity} BTC на сумму '
                   f'{order_info["cummulativeQuoteQty"]} TUSD по цене {order_info["price"]}')
        self.logger.info(message)
        self.send_message(message)
        return order_info

    def check_level(self, cur_price):
        """Проверяет, находится ли цена в допустимом для входа диапазоне."""
        intervals = LVL_C.keys()  # Содержит в себе нелинейные временные промежутки на таймфрейме
        data = CLIENT_BINANCE_OLD.klines('BTCTUSD', '1h', limit=24)  # В ответ на API-запрос получает свечи за период
        for dt in intervals:  # Для каждого из временных промежутков
            highs = []
            lows = []
            for data_hour in data[LVL_C[dt]['st']:LVL_C[dt]['end']]:  # Для каждого часа из промежутка
                highs.append(float(data_hour[2]))  # Добавляем наибольшее значение цены для часа в список
                lows.append(float(data_hour[3]))  # Добавляем наименьшее значение цены для часа в список
            width = max(highs) - min(lows)  # Находим длину коридора для временного промежутка
            if (max(highs) - LVL_C[dt]['hc1'] * width < cur_price < max(highs) + LVL_C[dt]['hc2'] * width or
                    min(lows) < cur_price < min(lows) + LVL_C[dt]['lc'] * width):  # Если цена в промежутке
                self.logger.debug(f'{self.name}: Проверены уровни для входа: False')
                return False  # Если цена находится в пределах толщины одного из уровней
            if width < 5 * cur_price * (COEF['OUTLET'] - 1):
                self.logger.debug(f'{self.name}: Проверены уровни для входа: False')
                return False  # Если волатильность не достаточна
        self.logger.debug(f'{self.name}: Проверены уровни для входа: True')
        return True  # Если цена не находится в пределах толщины одного из уровней
