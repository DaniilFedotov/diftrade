import time

from functions import get_logger
from classes import Trader


def main(bot):
    """Основная логика работы бота."""
    cur_depo = bot.get_balance('TUSD')
    while True:
        inlet_factor = bot.check_inlet_condition()  # Фактор входа, основанный на рандоме
        cur_price = bot.check_price()  # Проверяет текущую цену для проверки уровней
        level_factor = bot.check_level(cur_price)  # Фактор входа, основанный на уровнях
        bot.logger.debug(f'inlet_factor: {inlet_factor}, level_factor: {level_factor}')
        if inlet_factor and level_factor:  # Если оба фактора указывают на вход в сделку
            buy_info = bot.buy_coin(cur_depo)
            sell_info = None
            bot.logger.debug(f'buy_info: {buy_info}')
            if buy_info['status'] == 'FILLED':
                sell_info = bot.sell_coin(buy_info)
                bot.logger.debug(f'sell_info: {sell_info}')
            profit = float(sell_info['cummulativeQuoteQty']) - float(buy_info['cummulativeQuoteQty'])
            message = (f'{bot.name}: Сделка закрыта, заработок: '
                       f'{profit} TUSD '
                       f'Текущий депозит (ориентировочно): {sell_info["cummulativeQuoteQty"]} TUSD')
            cur_depo = sell_info["cummulativeQuoteQty"]
            bot.logger.info(message)
            bot.send_message(message)
        timer = bot.get_timer(param='SEARCH')
        time.sleep(timer)


if __name__ == "__main__":
    name = 'kittybot_margin_test'  # Имя торгового бота
    logger = get_logger(name)  # Получает логгер
    kittybot = Trader(name, logger)
    main(kittybot)
