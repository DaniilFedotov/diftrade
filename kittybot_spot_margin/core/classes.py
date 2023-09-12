from random import randint
import time

from telegram import TelegramError

from .constants import LVL_C, VLT_C, BOT_TG, RECVWINDOW, TELEGRAM_CHAT_ID


class Trader:  # Родительский класс для торговых ботов
    def __init__(self, name, logger, token, currency, client, coefficients):
        self.name = name
        self.logger = logger
        self.token = token
        self.currency = currency
        self.pair = token + currency
        self.client = client
        self.coefficients = coefficients

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
        return self.coefficients['CHECK_T']


class TraderSpotMargin(Trader):  # Класс для спотовой торговли
    def get_balance(self):
        """Показывает количество запрошенной монеты на аккаунте."""
        self.logger.debug(f'{self.name}: Проверил баланс {self.currency}')
        data = self.client.isolated_margin_account(symbols=self.pair, recvWindow=RECVWINDOW)
        return float(data['assets'][0]['quoteAsset']['free'])

    def check_inlet_condition(self):
        """Проверяет условие для входа, зависящее от версии бота."""
        random_factor = randint(1, int(self.coefficients['INLET']))  # Фактор входа, основанный на рандоме
        return random_factor == int(self.coefficients['INLET'])  # True/False

    def buy_coin(self, cur_depo, cur_price):
        """Выставляет рыночный ордер на покупку монеты."""
        try:
            quote = self.get_balance()
        except Exception:
            quote = cur_depo
            message = f'{self.name}: Баланс принят равным: {cur_depo} {self.currency}(Искл)'
            self.logger.error(message)
            self.send_message(message)
        quantity = quote * self.coefficients['MARGIN_RATIO'] / cur_price
        quantity_for_btc = quantity // 0.00001 / 100000  # Обрезает кол-во монет под нужный формат
        params = {
            "symbol": self.pair,  # Тикер токена
            "isIsolated": True,
            "side": "BUY",  # Покупка
            "type": "LIMIT",  # Тип ордера - рыночный
            "quantity": quantity_for_btc,  # Количество. Другой вариант - quoteOrderQty
            "price": cur_price,
            "sideEffectType": "MARGIN_BUY",  # Автозаем
            "timeInForce": "GTC",
            "recvWindow": RECVWINDOW,
        }
        response = self.client.new_margin_order(**params)  # Открывает лимитный ордер на покупку по указанной цене
        order_id = str(response['orderId'])
        order_info = self.client.margin_order(symbol=self.pair, orderId=order_id, recvWindow=RECVWINDOW)
        order_status = order_info['status']
        while order_status != 'FILLED':
            timer = self.get_timer(param='CHECK_T')
            time.sleep(timer)
            order_info = self.client.margin_order(self.pair, orderId=order_id, recvWindow=RECVWINDOW)
            order_status = order_info['status']
            message = (f'{self.name}: Проверено состояние ордера:'
                       f'{order_info}, status: {order_status}')
            self.logger.debug(message)
        message = (f'{self.name}: Куплено {response["origQty"]} {self.token} на сумму '
                   f'{response["cummulativeQuoteQty"]} {self.currency} по цене {response["fills"][0]["price"]}')
        self.logger.info(message)
        self.send_message(message)
        return response

    def sell_coin(self, buy_info):
        """Выставляет ОСО ордер на продажу монеты по заданной цене."""
        quantity = float(buy_info['origQty'])
        price = float(buy_info['cummulativeQuoteQty']) / quantity
        sell_price = int(price * self.coefficients['OUTLET'])
        stop_price = int(price * self.coefficients['STOP'])
        stop_limit = int(price * self.coefficients['STOP_LIMIT'])
        params = {
            "symbol": self.pair,  # Тикер токена
            "isIsolated": True,
            "side": "SELL",  # Продажа
            "quantity": quantity,  # Количество монет
            "price": sell_price,  # Заданная цена
            "stopPrice": stop_price,  # Цена, при которой выставляется лимитная заявка на продажу по стопу
            "stopLimitPrice": stop_limit,  # Цена, по которой продается монета по стопу
            "sideEffectType": 'AUTO_REPAY',  # Автопогашение
            "stopLimitTimeInForce": "GTC",
            "recvWindow": RECVWINDOW,  # Необходимо для предотвращения ошибки 1021
        }
        response = self.client.new_margin_oco_order(**params)  # Открывает ордер на продажу со стопом
        stop_order_id = str(response['orders'][0]['orderId'])
        limit_order_id = str(response['orders'][1]['orderId'])
        stop_order_info = self.client.get_order(symbol=self.pair, orderId=stop_order_id, recvWindow=RECVWINDOW)
        limit_order_info = self.client.get_order(symbol=self.pair, orderId=limit_order_id, recvWindow=RECVWINDOW)
        stop_order_status = stop_order_info['status']
        limit_order_status = limit_order_info['status']
        while stop_order_status != 'FILLED' and limit_order_status != 'FILLED':
            timer = self.get_timer(param='CHECK_T')
            time.sleep(timer)
            stop_order_info = self.client.get_order(self.pair, orderId=stop_order_id, recvWindow=RECVWINDOW)
            limit_order_info = self.client.get_order(self.pair, orderId=limit_order_id, recvWindow=RECVWINDOW)
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
        message = (f'{self.name}: Продано {quantity} {self.token} на сумму '
                   f'{order_info["cummulativeQuoteQty"]} {self.currency} по цене {order_info["price"]}')
        self.logger.info(message)
        self.send_message(message)
        return order_info

    def check_level(self, cur_price):
        """Проверяет, находится ли цена в допустимом для входа диапазоне."""
        data_24h = self.client.klines(self.pair, '1h', limit=24)  # В ответ на API-запрос получает свечи за период
        #data_60m = self.client.klines(self.pair, '5m', limit=12)  # В ответ на API-запрос получает свечи за период
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
