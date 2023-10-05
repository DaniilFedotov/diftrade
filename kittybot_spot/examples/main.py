import time

from functions import get_logger
from classes import TraderSpot
from constants import TRADER_NAME, TOKEN_NAME, CURRENCY, CLIENT_BINANCE_F


def main(bot):
    """Основная логика работы бота."""
    cur_depo = bot.get_balance()
    while True:
        inlet_factor = bot.check_inlet_condition()  # Фактор входа, основанный на рандоме
        cur_price = bot.check_price()  # Проверяет текущую цену для проверки уровней
        level_factor = bot.check_level(cur_price)  # Фактор входа, основанный на уровнях
        bot.logger.debug(f'inlet_factor: {inlet_factor}, level_factor: {level_factor}')
        if inlet_factor and level_factor:  # Если оба фактора указывают на вход в сделку
            buy_info = bot.buy_coin(cur_depo, cur_price)
            sell_info = None
            bot.logger.debug(f'buy_info: {buy_info}')
            if buy_info['status'] == 'FILLED':
                sell_info = bot.sell_coin(buy_info)
                bot.logger.debug(f'sell_info: {sell_info}')
            profit = float(sell_info['cummulativeQuoteQty']) - float(buy_info['cummulativeQuoteQty'])
            message = (f'{bot.name}: Сделка закрыта, заработок: '
                       f'{profit} {bot.currency} '
                       f'Текущий депозит (ориентировочно): {sell_info["cummulativeQuoteQty"]} {bot.currency}')
            cur_depo = sell_info["cummulativeQuoteQty"]
            bot.logger.info(message)
            bot.send_message(message)
        timer = bot.get_timer(param='SEARCH')
        time.sleep(timer)


if __name__ == "__main__":
    logger = get_logger(TRADER_NAME)  # Получает логгер
    trader_bot = TraderSpot(
        TRADER_NAME,
        logger,
        TOKEN_NAME,
        CURRENCY,
        CLIENT_BINANCE_F
    )
    main(trader_bot)
