import os

from dotenv import load_dotenv

from binance.spot import Spot

load_dotenv()  # Загружает секретные ключи

BINANCE_TOKEN_S = os.getenv('BINANCE_TOKEN_S')  # Ключ для S
BINANCE_KEY_S = os.getenv('BINANCE_SECRET_KEY_S')  # Ключ для S
CLIENT_BINANCE_S = Spot(api_key=BINANCE_TOKEN_S, api_secret=BINANCE_KEY_S)  # Регистрируем клиента для API-binance

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
account = CLIENT_BINANCE_S.isolated_margin_account(symbols='BTCTUSD')
print(account)
response = CLIENT_BINANCE_S.new_margin_order(
    symbol='BTCTUSD',
    side='BUY',
    type='LIMIT',
    quantity=0.015,
    price='28000',
    timeInForce='GTC',
    isIsolated=True,
)
print(response)