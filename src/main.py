import asyncio
import json
import logging
import time
from decimal import Decimal

from core.log import logger
from schemas.setting import Setting
from services.bot.triggers import OrderbookTrigger
from api.bybit_client import BybitClient
from services.bot import Side, TradeRange, OrderbookBridge

# Получаем настройки бота
with open("settings.json", "r") as file:
    settingText = file.read()
settings = Setting(**json.loads(settingText))
if settings.side == 0:
    side = Side.Buy
else:
    side = Side.Sell

client = BybitClient(
    key=settings.key,
    secret_key=settings.secret_key
)

orderbook_bridge = OrderbookBridge(
    symbol=settings.symbol,
    client=client,
    category="spot"
)
trigger = None

def on_channel_change_signal(side: Side):
    logger.info(side)
    time.sleep(1)
    trigger.restart()


def get_marker_trade_range():
    data = client.get_orderbook(symbol=settings.symbol, category="spot")

    trade_range = {
        'trade_range': TradeRange(sell=data.asks[0].price, buy=data.bids[0].price),
        'ask_size': data.asks[0].size - 1000,
        'bid_size': data.bids[0].size - 1000
    }

    return trade_range


trade_range = get_marker_trade_range()

trigger = OrderbookTrigger(
    orderbook_bridge=orderbook_bridge,
    trade_range=trade_range["trade_range"],
    min_ask_size=trade_range["ask_size"],
    min_bid_size=trade_range["bid_size"],
    on_triggered=on_channel_change_signal
)


while True:
    time.sleep(1)
