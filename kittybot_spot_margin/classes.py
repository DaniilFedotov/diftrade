from random import randint
import time

from telegram import TelegramError

from constants import COEF, LVL_C, VLT_C, CLIENT_BINANCE_D, CLIENT_BINANCE_S, BOT_TG, RECVWINDOW, TELEGRAM_CHAT_ID


class Trader:  # Родительский класс для торговых ботов
    def __init__(self, name, logger):
        self.name = name
        self.logger = logger

    def check_price(self):
        """Проверяет цену монеты."""
        try:
            price = float(CLIENT_BINANCE_D.ticker_price('BTCTUSD')["price"])  # В ответ на запрос получает цену токена
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

    def get_timer(self, param):
        """Определяет время следующего запроса к API в зависимости от исхода."""
        self.logger.debug(f'{self.name}: Определил время следующего запроса')
        if param == 'STOP':
            return 150 * 60
        elif param == 'SEARCH':
            return 30
        return COEF['CHECK_T']