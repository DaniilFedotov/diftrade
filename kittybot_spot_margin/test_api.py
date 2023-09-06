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
# Лимитный маржин ордер
# response = CLIENT_BINANCE_S.new_margin_order(
#     symbol='BTCTUSD',
#     isIsolated=True,
#     side='BUY',
#     type='LIMIT',
#     quantity=0.0397,
#     price='25000',
#     sideEffectType='MARGIN_BUY',
#     timeInForce='GTC',
# )

# Рыночный маржин ордер
# response = CLIENT_BINANCE_S.new_margin_order(
#     symbol='BTCTUSD',
#     isIsolated=True,
#     side='BUY',
#     type='MARKET',
#     quantity=0.018,
#     sideEffectType='MARGIN_BUY',
# )

# Лимит ОСО ордер на продажу
response = CLIENT_BINANCE_S.new_margin_oco_order(
    symbol='BTCTUSD',
    isIsolated=True,
    side='SELL',
    quantity=0.018,
    price=25000,
    stopPrice=30000,
    stopLimitPrice=20000,
    sideEffectType='AUTO_REPAY',
    # сверить со спотом и сделать как там + по доке, затем затестить
)
print(response)
