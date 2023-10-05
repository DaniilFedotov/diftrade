import os
import time

from dotenv import load_dotenv

from binance.spot import Spot

load_dotenv()  # Загружает секретные ключи

BINANCE_TOKEN_S = os.getenv('BINANCE_TOKEN_SECOND')  # Токен для API-binance
BINANCE_KEY_S = os.getenv('BINANCE_SECRET_KEY_SECOND')  # Ключ для API-binance
CLIENT_BINANCE_S = Spot(api_key=BINANCE_TOKEN_S, api_secret=BINANCE_KEY_S)  # Регистрация клиента API-binance
"""
BINANCE_TOKEN_F = os.getenv('BINANCE_TOKEN_FIRST')  # Токен для API-binance
BINANCE_KEY_F = os.getenv('BINANCE_SECRET_KEY_FIRST')  # Ключ для API-binance
CLIENT_BINANCE_F = Spot(api_key=BINANCE_TOKEN_F, api_secret=BINANCE_KEY_F)
"""


RECVWINDOW = 59000
"""
result = CLIENT_BINANCE_S.margin_account()
tokens = result['userAssets']
for tiker in tokens:
    if tiker['free'] != '0':
        tusd_value = int(tiker['free'])
        print(tiker)
print(tusd_value)

"""
# get_balance
# account = CLIENT_BINANCE_S.isolated_margin_account(symbols='BTCTUSD', recvWindow=RECVWINDOW)
# print(account)
# data = account['assets'][0]['quoteAsset']['free']
# print(data)


# Лимитный маржин ордер
# response = CLIENT_BINANCE_S.new_margin_order(
#     symbol='BTCTUSD',
#     isIsolated=True,
#     side='BUY',
#     type='LIMIT',
#     quantity=0.0005,
#     price=25940,
#     sideEffectType='MARGIN_BUY',
#     timeInForce='GTC',
# )
# print(response)
# order_id = response['orderId']
print(f'timestamp: {time.time()}')
order_id = 3000911208
# print(order_id)
order_info = CLIENT_BINANCE_S.margin_order(symbol='BTCTUSD', orderId=order_id, isIsolated=True, recvWindow=RECVWINDOW)
print(f'order info : {order_info}')
print(f'ordertime: {order_info["time"]}')
trades = CLIENT_BINANCE_S.margin_my_trades(
    symbol='BTCTUSD',
    isIsolated=True,
    #startTime=order_info["time"],
    recvWindow=RECVWINDOW)
for trade in trades:
    print(f'id: {trade["orderId"]}, commission:{trade["commission"]}, qty: {trade["qty"]}, time: {trade["time"]}')
# print(f'trades: {trades}')

# fills = response['fills']
# for fill in fills:
#     commission = float(fill['commission'])
#     print(f'commission: {commission}')
#     if commission != 0:
#         print('остановили бота')

# Получаем ордер
# pair = 'BTCTUSD'
# order_id = 2996554060
# order_id = response['orderId']
# print(order_id)
# order_info = CLIENT_BINANCE_S.margin_order(symbol=pair, orderId=order_id, isIsolated=True, recvWindow=RECVWINDOW)
# print(f'order info : {order_info}')
# order_status = order_info['status']
# print('first try')
# print(f'response: {response}\n'
#       f'order_id: {order_id}\n'
#       f'order_info: {order_info}\n'
#       f'order_status: {order_status}')


# Рыночный маржин ордер
# response = CLIENT_BINANCE_S.new_margin_order(
#     symbol='BTCTUSD',
#     isIsolated=True,
#     side='BUY',
#     type='MARKET',
#     quantity=0.001,
#     sideEffectType='MARGIN_BUY',
# )
# print(response)

# params = {
#     "symbol": 'BTCTUSD',  # Тикер токена
#     "side": "BUY",  # Покупка
#     "type": "MARKET",  # Тип ордера - рыночный
#     "quantity": 0.001,  # Количество. Другой вариант - quoteOrderQty
# }
# response2 = CLIENT_BINANCE_F.new_order(**params)  # Открывает ордер на покупку по рыночной цене
# print(f'response через маржу: {response}'
#       f'response через спот: {response2}')

# Лимит ОСО ордер на продажу
# response = CLIENT_BINANCE_S.new_margin_oco_order(
#     symbol='BTCTUSD',
#     isIsolated=True,
#     side='SELL',
#     quantity=0.018,
#     price=25785,
#     stopPrice=22000,
#     stopLimitPrice=21980,
#     sideEffectType='AUTO_REPAY',
#     stopLimitTimeInForce="GTC",
#     recvWindow=RECVWINDOW,
# )
#print(response)
