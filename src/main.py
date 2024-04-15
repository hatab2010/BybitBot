import json
from time import sleep
from schemas.setting import Setting
from src.api.bybit_client import BybitClient
from services.bot import TimeRangeTrigger, Side, TradeRange
from src.services.bot import BybitBotService

# Получаем настройки бота
with open("settings.json", "r") as file:
    settingText = file.read()
settings = Setting.from_dict(json.loads(settingText))
if settings.side == 0:
    side = Side.Buy
else:
    side = Side.Sell

client = BybitClient(
        is_testnet=settings.is_testnet,
        key=settings.key,
        secret_key=settings.secret_key
)

print(client.get_order_history(symbol="USDCUSDT"))

# trade_range = Range(
#     top=settings.sellPrice,
#     bottom=settings.buyPrice
# )
# trade_trigger = TimeRangeTrigger(
#     target_range=trade_range,
#     trigger_duration_buy=settings.triggerDurationBuy,
#     trigger_duration_sell=settings.triggerDurationSell
# )
# trade_bot = BybitBotService(
#     qty=settings.tradeAmount,
#     trade_range=Range(
#         top=settings.sellPrice,
#         bottom=settings.buyPrice
#     ),
#     trigger=trade_trigger,
#     client=client,
#     allow_range=Range(
#         top=settings.allowTopPrice,
#         bottom=settings.allowBottomPrice
#     ),
#     overlap_top_price=settings.overlapSellPrice,
#     symbol=settings.symbol
# )
#
# sleep(3)
# trade_bot.set_orders_count(settings.orderCount, side)
# while True:
#     sleep(1)
