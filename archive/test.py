import os
import random
from dotenv import load_dotenv
from binance.spot import Spot

DEF = {  # DEFINITION, коэф-ты для проверки уровней. Определяют толщину уровня и длину участка
    12: {'hc': 0.2,  # high_coef
         'lc': 0.1,  # low-coef
         'st': 0,  # start - начало интервала
         'end': 12},  # end - конец интервала
    6: {'hc': 0.18,
        'lc': 0.09,
        'st': 12,
        'end': 18},
    3: {'hc': 0.16,
        'lc': 0.08,
        'st': 18,
        'end': 21},
    2: {'hc': 0.14,
        'lc': 0.07,
        'st': 21,
        'end': 23},
    1: {'hc': 0.12,
        'lc': 0.06,
        'st': 23,
        'end': 24}
}
load_dotenv()  # Загружает секретные ключи

BINANCE_TOKEN = os.getenv('BINANCE_TOKEN_SDK')  # Токен для версии через SDK
BINANCE_KEY = os.getenv('BINANCE_SECRET_KEY_SDK')  # Ключ для версии через SDK
client = Spot(api_key=BINANCE_TOKEN, api_secret=BINANCE_KEY)


def check_level(current_price):
    """Проверяет, находится ли цена в допустимом для входа диапазоне."""
    intervals = DEF.keys()  # Содержит в себе нелинейные временные промежутки на таймфрейме
    data = client.klines('BTCTUSD', '1h', limit=24)  # В ответ на API-запрос получает свечи за указанный период
    # print(f'data:{data}')
    for interval in intervals:  # Для каждого из временных промежутков
        highs = []
        lows = []
        for data_hour in data[DEF[interval]['st']:DEF[interval]['end']]:  # Для каждого часа из временного промежутка
            # print(f'interval: {interval}')
            # print(f'data hour: {data_hour}')
            highs.append(float(data_hour[2]))  # Добавляем наибольшее значение цены для часа в список
            lows.append(float(data_hour[3]))  # Добавляем наименьшее значение цены для часа в список
        width = max(highs) - min(lows)  # Находим длину коридора для временного промежутка
        # print(width)
        # print(f'highs: {highs}, lows: {lows}')
        if (max(highs) - DEF[interval]['hc'] * width < current_price < max(highs) or
                min(lows) < current_price < min(lows) + DEF[interval]['lc'] * width):
            return False  # Если цена находится в пределах толщины одного из уровней
    return True  # Если цена не находится в пределах толщины одного из уровней


def main():
    """Основная логика работы бота."""
    quote = 100
    params = {
        "symbol": "BTCTUSD",  # Тикер токена
        "side": "BUY",  # Покупка
        "type": "MARKET",  # Тип ордера - рыночный
        "quoteOrderQty": quote,  # Сумма TUSD на ордер
    }
    # response = client.new_order(**params)  # Открывает ордер на покупку по рыночной цене
    # response = client.get_order("BTCTUSD", orderId='934685944')
    order_info = client.get_order("BTCTUSD", orderId='983324033')
    status = order_info['status']
    print(order_info)
    print(status)


if __name__ == "__main__":
    main()
