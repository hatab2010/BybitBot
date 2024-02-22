import json
from time import sleep
from data import Setting
from models import BybitClient
from src.services import BybitBotService, Range, TimeRangeTrigger

# Получаем настройки бота
with open("src/settings.json", "r") as file:
    settingText = file.read()
settings = Setting.from_dict(json.loads(settingText))

trade_range = Range(
    top=settings.sellPrice,
    bottom=settings.buyPrice
)

trade_trigger = TimeRangeTrigger(
    target_range=trade_range,
    trigger_duration=settings.triggerDuration,
    accept_height=trade_range.height
)

trade_bot = BybitBotService(
    qty=settings.tradeAmount,
    trade_range=Range(
        top=settings.sellPrice,
        bottom=settings.buyPrice
    ),
    trigger=trade_trigger,
    client=BybitClient(
        is_testnet=settings.isTestnet,
        key=settings.key,
        secret_key=settings.secretKey
    ),
    allow_range=Range(
        top=settings.allowTopPrice,
        bottom=settings.allowBottomPrice
    ),
    overlap_top_price=settings.overlapSellPrice
)

trade_bot.set_symbol(settings.symbol)
sleep(3)
trade_bot.start(settings.orderCount)

while True:
    sleep(1)
