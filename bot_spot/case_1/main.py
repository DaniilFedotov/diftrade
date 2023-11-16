import time

from ..core.functions import get_logger
from ..core.classes import TraderSpotOld
from ..core.constants import (TRADER_NAME, TOKEN_NAME,
                              CURRENCY, CLIENT_BINANCE_S)


def main(bot):
    """Основная логика работы бота."""
    cur_depo = bot.get_balance()
    while True:
        inlet_factor = bot.check_inlet_condition()
        cur_price = bot.check_price()  # Проверяет текущую цену
        level_factor = bot.check_level(cur_price)
        bot.logger.debug(f'inlet_factor: {inlet_factor}, '
                         f'level_factor: {level_factor}')
        if inlet_factor and level_factor:  # Вход в сделку
            buy_info = bot.buy_coin(cur_depo, cur_price)
            sell_info = None
            bot.logger.debug(f'buy_info: {buy_info}')
            if buy_info['status'] == 'FILLED':
                sell_info = bot.sell_coin(buy_info)
                bot.logger.debug(f'sell_info: {sell_info}')
            profit = (float(sell_info['cummulativeQuoteQty']) -
                      float(buy_info['cummulativeQuoteQty']))
            message = (f'{bot.name}: Сделка закрыта, заработок: '
                       f'{profit} {bot.currency} '
                       f'Текущий депозит (ориентировочно): '
                       f'{sell_info["cummulativeQuoteQty"]} {bot.currency}')
            cur_depo = sell_info['cummulativeQuoteQty']
            bot.logger.info(message)
            bot.send_message(message)
        timer = bot.get_timer(param='SEARCH')
        time.sleep(timer)


if __name__ == '__main__':
    logger = get_logger(TRADER_NAME)  # Получает логгер
    trader_bot = TraderSpotOld(
        TRADER_NAME,
        logger,
        TOKEN_NAME,
        CURRENCY,
        CLIENT_BINANCE_S
    )
    main(trader_bot)
