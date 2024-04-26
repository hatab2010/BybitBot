import json
import time
from decimal import Decimal

from domain_models import CoinType, TradeRange
from schemas.setting import Setting
from services.bot.socket_bridges import OrderBridge, TickerBridge
from api.bybit_client import BybitClient
from services.bot import Side, OrderbookBridge, OrderManager, BotOptions, BybitBotService, TimeRangeTrigger, \
    OrderbookTrigger

client = None


def get_market_trade_range(symbol: str, category: str) -> TradeRange:
    orderbook = client.get_orderbook(
        category=category,
        symbol=symbol
    )

    return TradeRange(orderbook.bids[0].price, orderbook.asks[0].price)


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

target_range = get_market_trade_range(
    symbol=settings.symbol,
    category="spot"
)

target_range.offset(2)

orderbook_bridge = OrderbookBridge(
    symbol=settings.symbol,
    client=client,
    category="spot"
)

order_bridge = OrderBridge(
    symbol=settings.symbol,
    client=client,
    category="private"
)

ticker_bridge = TickerBridge(
    symbol=settings.symbol,
    client=client,
    category="spot"
)

bot_options = BotOptions(
    category="spot",
    symbol=settings.symbol,
    trade_range=target_range,
    allow_range=TradeRange(settings.allow_bottom_price, settings.allow_top_price),
    overlap_top_price=settings.overlap_sell_price,
    qty=settings.trade_amount
)

time_trigger = TimeRangeTrigger(
    target_range=target_range,
    ticker_bridge=ticker_bridge,
    trigger_duration_buy=settings.trigger_duration_buy,
    trigger_duration_sell=settings.trigger_duration_sell
)

orderbook_trigger = OrderbookTrigger(
    orderbook_bridge=orderbook_bridge,
    trade_range=target_range,
    min_bid_size=settings.min_bid_size,
    min_ask_size=settings.min_ask_size
)

bot = BybitBotService(
    order_bridge=order_bridge,
    client=client,
    options=bot_options,
    time_trigger=time_trigger,
    orderbook_trigger=orderbook_trigger
)

# manager = OrderManager(
#     client=client,
#     order_bridge=order_bridge,
#     symbol=settings.symbol,
#     category="spot"
# )


while True:
    time.sleep(1)
