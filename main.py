from pybit.unified_trading import HTTP, WebSocket
from time import sleep
from data import Setting
import json
from colorama import Fore, Back, Style
from data import Setting, WebsocketResponse
from models import BybitClient

with open("settings.json", "r") as file:
    settingText = file.read()
settings = Setting.from_dict(json.loads(settingText))

def callback(data):
    with open("settings.json", "r") as file:
        st = file.read()
    p = Setting.from_dict(json.loads(st))
    print("--handle--")
    print(data)
    try:
        responce = WebsocketResponse.from_dict(data)

        if responce.data[0].orderStatus == "Filled":
            if responce.data[0].side == "Buy":
                ctx_price = settings.sellPrice,
                ctx_side = "Sell"
            else:
                ctx_price = settings.buyPrice
                ctx_side = "Buy"
            print(ctx_price)

            #TODO заплатка. Какой-то пидр картежит поле
            try:
                client.place_order(
                    symbol=settings.symbol,
                    side=ctx_side,
                    price=ctx_price,
                    qty=settings.tradeAmount
                )
            except:
                client.place_order(
                    symbol=settings.symbol,
                    side=ctx_side,
                    price=ctx_price[0],
                    qty=settings.tradeAmount
                )

        pass
    except Exception as ex:
        print(ex)
        pass


def handle_message(message: str):
    print("--handle--")
    print(message)
    try:
        responce = WebsocketResponse.from_dict(json.loads(message))
        if responce.data[0].orderStatus == "Filled":
            if responce.data[0].side == "Buy":
                ctx_price = settings.sellPrice,
                ctx_side = "Sell"
            else:
                ctx_price = settings.buyPrice
                ctx_side = "Buy"

            client.place_order(
                symbol=settings.symbol,
                side=ctx_side,
                price=ctx_price,
                qty=settings.tradeAmount
            )
        pass
    except Exception as ex:
        pass


client = BybitClient(
    secret_key=settings.secretKey,
    is_testnet=settings.isTestnet,
    key=settings.key,
    websocket_callback=callback,
    handler=handle_message
)
sleep(2)
#Первая закупка
for number in range(settings.orderCount):
    client.place_order(
        symbol=settings.symbol,
        qty=settings.tradeAmount,
        price=settings.buyPrice,
        side="Buy"
    )

while True:
    sleep(1)
