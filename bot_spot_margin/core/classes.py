from random import randint
import time

from telegram import TelegramError

from .constants import (LVL_C, VLT_C, BOT_TG, RECVWINDOW, TELEGRAM_CHAT_ID,
                        TIMEDELTA_COMMISSION, SLEEPTIME_COMMISSION,
                        PRICE_DELTA_BTC, BUY_ORDER_LIFETIME)


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
            price = float(self.client.ticker_price(self.pair)['price'])
            self.logger.debug(
                f'{self.name}: Цена проверена: {price} {self.currency}')
            return price
        except Exception as error:
            message = f'Ошибка при проверке цены: {error}'
            self.logger.error(message)
            self.send_message(message)
            raise Exception(message)

    def send_message(self, message):
        """Отправляет сообщение в Telegram чат."""
        try:
            BOT_TG.send_message(TELEGRAM_CHAT_ID, message)
            self.logger.debug(
                f'Сообщение в Telegram отправлено: {message}')
        except TelegramError:
            self.logger.error(
                f'Сбой при отправке сообщения в Telegram: {message}')

    def get_timer(self, param):
        """Определяет время следующего запроса к API
        в зависимости от исхода.
        """
        self.logger.debug(f'{self.name}: Определил время следующего запроса\n'
                          f'-----------------------------------------------')
        if param == 'STOP':
            return 150 * 60
        elif param == 'SEARCH':
            return 30
        return self.coefficients['CHECK_T']


class TraderSpotMargin(Trader):  # Класс для спотовой торговли
    def get_balance(self):
        """Показывает количество запрошенной монеты на аккаунте."""
        self.logger.debug(f'{self.name}: Проверил баланс {self.currency}')
        data = self.client.isolated_margin_account(symbols=self.pair)
        balance = float(data['assets'][0]['quoteAsset']['free'])
        self.logger.debug(f'{self.name}: Баланс составляет '
                          f'{balance} {self.currency}')
        return float(data['assets'][0]['quoteAsset']['free'])

    def check_inlet_condition(self):
        """Проверяет условие для входа, зависящее от версии бота."""
        random_factor = randint(1, int(self.coefficients['INLET']))
        return random_factor == int(self.coefficients['INLET'])

    def check_commission(self):
        """Проверяет размер комиссии для сделок,
        совершенных в течение заданного промежутка времени.
        """
        # Приводит к формату binance
        now_timestamp = int(time.time()) * 1000
        trades = self.client.margin_my_trades(
            symbol=self.pair,
            isIsolated=True,
            startTime=now_timestamp-TIMEDELTA_COMMISSION,
            recvWindow=RECVWINDOW)
        for trade in trades:
            if float(trade['commission']) != 0:
                message = f'{self.name}: Комиссия не нулевая!'
                self.logger.error(message)
                self.send_message(message)
                time.sleep(SLEEPTIME_COMMISSION)
        message = f'{self.name}: Комиссия нулевая.'
        self.logger.debug(message)

    def buy_coin(self, cur_depo, cur_price):
        """Выставляет рыночный ордер на покупку монеты."""
        try:
            quote = self.get_balance()
        except Exception:
            quote = cur_depo
            message = (f'{self.name}: Баланс принят равным: '
                       f'{cur_depo} {self.currency}(Искл)')
            self.logger.error(message)
            self.send_message(message)
        quantity = quote * self.coefficients['MARGIN_RATIO'] / cur_price
        # Обрезает кол-во монет под нужный формат
        quantity_for_btc = quantity // 0.00001 / 100000
        params = {
            'symbol': self.pair,
            'isIsolated': True,
            'side': 'BUY',
            'type': 'LIMIT',
            # Количество. Другой вариант - quoteOrderQty
            'quantity': quantity_for_btc,
            'price': cur_price - PRICE_DELTA_BTC,
            # Автозаем
            # 'sideEffectType': 'MARGIN_BUY',
            'timeInForce': 'GTC',
            'recvWindow': RECVWINDOW,
        }
        # Открывает лимитный ордер на покупку по указанной цене
        response = self.client.new_margin_order(**params)
        order_id = str(response['orderId'])
        message = (f'{self.name}: Открыт лимитный ордер на покупку. '
                   f'order_id: {order_id}')
        self.logger.debug(message)
        while True:
            timer = self.get_timer(param='CHECK_T')
            time.sleep(timer)
            order_info = self.client.margin_order(
                symbol=self.pair,
                orderId=order_id,
                isIsolated=True,
                recvWindow=RECVWINDOW)
            order_status = order_info['status']
            message = (f'{self.name}: Проверено состояние ордера:'
                       f'{order_info}, status: {order_status}')
            self.logger.debug(message)
            if order_status == 'FILLED':
                self.check_commission()
                message = (f'{self.name}: Куплено {order_info["origQty"]} '
                           f'{self.token} на сумму '
                           f'{order_info["cummulativeQuoteQty"]} '
                           f'{self.currency} по цене {order_info["price"]}')
                self.logger.info(message)
                self.send_message(message)
                return order_info
            elif order_status == 'CANCELED':
                self.logger.info('Ордер отменен не программным путем.')
                return 'canceled'
            elif order_status == 'NEW':
                now_timestamp = int(time.time()) * 1000
                order_time = order_info['time']
                if now_timestamp - order_time >= BUY_ORDER_LIFETIME:
                    self.client.cancel_margin_order(
                        symbol=self.pair,
                        orderId=order_id,
                        isIsolated=True,
                        recvwindow=RECVWINDOW)
                    self.logger.info('Ордер отменен программным путем.')
                    return 'canceled'

    def sell_coin(self, buy_info):
        """Выставляет ОСО ордер на продажу монеты по заданной цене."""
        quantity = float(buy_info['origQty'])
        price = float(buy_info['cummulativeQuoteQty']) / quantity
        sell_price = int(price * self.coefficients['OUTLET'])
        stop_price = int(price * self.coefficients['STOP'])
        stop_limit = int(price * self.coefficients['STOP_LIMIT'])
        params = {
            'symbol': self.pair,
            'isIsolated': True,
            'side': 'SELL',
            'quantity': quantity,
            'price': sell_price,
            # Цена, при которой выставляется лимитная заявка на продажу по стоп
            'stopPrice': stop_price,
            # Цена, по которой продается монета по стопу
            'stopLimitPrice': stop_limit,
            # Автопогашение
            'sideEffectType': 'AUTO_REPAY',
            'stopLimitTimeInForce': 'GTC',
            # Необходимо для предотвращения ошибки 1021
            'recvWindow': RECVWINDOW,
        }
        # Открывает ордер на продажу со стопом
        response = self.client.new_margin_oco_order(**params)
        stop_order_id = str(response['orders'][0]['orderId'])
        limit_order_id = str(response['orders'][1]['orderId'])
        stop_order_info = self.client.margin_order(
            symbol=self.pair,
            orderId=stop_order_id,
            isIsolated=True,
            recvWindow=RECVWINDOW)
        limit_order_info = self.client.margin_order(
            symbol=self.pair,
            orderId=limit_order_id,
            isIsolated=True,
            recvWindow=RECVWINDOW)
        stop_order_status = stop_order_info['status']
        limit_order_status = limit_order_info['status']
        while stop_order_status != 'FILLED' and limit_order_status != 'FILLED':
            timer = self.get_timer(param='CHECK_T')
            time.sleep(timer)
            stop_order_info = self.client.margin_order(
                symbol=self.pair,
                orderId=stop_order_id,
                isIsolated=True,
                recvWindow=RECVWINDOW)
            limit_order_info = self.client.margin_order(
                symbol=self.pair,
                orderId=limit_order_id,
                isIsolated=True,
                recvWindow=RECVWINDOW)
            stop_order_status = stop_order_info['status']
            limit_order_status = limit_order_info['status']
            message = (f'{self.name}: Проверено состояние ордеров:'
                       f'{stop_order_info}, status: {stop_order_status},'
                       f'{limit_order_info}, status: {limit_order_status},')
            # self.logger.debug(message)
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
            self.logger.error(message)
            self.send_message(message)
            timer = self.get_timer(param='STOP')
            time.sleep(timer)
        message = (f'{self.name}: Продано {quantity} {self.token} '
                   f'на сумму {order_info["cummulativeQuoteQty"]} '
                   f'{self.currency} по цене {order_info["price"]}')
        self.logger.info(message)
        self.send_message(message)
        return order_info

    def check_level(self, cur_price):
        """Проверяет, находится ли цена в допустимом для входа диапазоне."""
        # В ответ на API-запрос получает свечи за период
        data_24h = self.client.klines(self.pair, '1h', limit=24)
        # В ответ на API-запрос получает свечи за период
        # data_60m = self.client.klines(self.pair, '5m', limit=12)
        checks_box = []
        check_first = self.check_global_level(cur_price, data_24h)
        checks_box.append(check_first)
        check_second = self.check_admissible_volatility(cur_price, data_24h)
        checks_box.append(check_second)
        # check_third = self.check_small_timeframe(cur_price, data_60m)
        # checks_box.append(check_third)

        for check in checks_box:
            if not check:
                self.logger.debug(f'{self.name}: Глобальная проверка: False')
                # Вход в сделку не допускается
                return False
        self.logger.debug(f'{self.name}: Глобальная проверка: True')
        # Вход в сделку допускается
        return True

    def check_global_level(self, cur_price, data_24h):
        """Проверяет, находится ли текущая цена
        в пределах глобальных уровней.
        """
        intervals = LVL_C.keys()
        for dt in intervals:
            highs = []
            lows = []
            for data_hour in data_24h[LVL_C[dt]['st']:LVL_C[dt]['end']]:
                highs.append(float(data_hour[2]))
                lows.append(float(data_hour[3]))
            width = max(highs) - min(lows)
            if (max(highs) - LVL_C[dt]['hc1'] * width < cur_price <
                    max(highs) + LVL_C[dt]['hc2'] * width or
                    min(lows) < cur_price <
                    min(lows) + LVL_C[dt]['lc'] * width):
                self.logger.debug(f'{self.name}: Проверены уровни для '
                                  f'входа: False. Проверку уровней не '
                                  f'прошел промежуток: {dt}')
                # Если цена находится в пределах одного из уровней
                return False
        self.logger.debug(f'{self.name}: Проверены уровни для входа: True')
        # Если цена не находится в пределах одного из уровней
        return True

    def check_admissible_volatility(self, cur_price, data_24h):
        """Проверяет, находится ли текущая волатильность
        в пределах допустимой величины.
        """
        intervals = VLT_C.keys()
        for dt in intervals:
            highs = []
            lows = []
            for data_hour in data_24h[VLT_C[dt]['st']:VLT_C[dt]['end']]:
                highs.append(float(data_hour[2]))
                lows.append(float(data_hour[3]))
            width = max(highs) - min(lows)
            if (width < VLT_C[dt]['lvc'] * cur_price or
                    width > VLT_C[dt]['hvc'] * cur_price):
                self.logger.debug(f'{self.name}: Проверена волатильность: '
                                  f'False. Проверку волатильности не прошел '
                                  f'промежуток: {dt}')
                # Если волатильность не находится в пределах допустимой
                return False
        self.logger.debug(f'{self.name}: Проверена волатильность: True')
        # Если волатильность находится в пределах допустимой
        return True

    def check_small_timeframe(self, cur_price, data_60m):
        """Проверяет, не находится ли текущая цена
        в зоне перекупленности на малом таймфрейме.
        """
        return True
