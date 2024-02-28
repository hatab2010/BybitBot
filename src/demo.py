import json
from time import sleep
from data import Setting
from models import BybitClient
from pybit.unified_trading import WebSocket, HTTP

# Получаем настройки бота
with open("settings.json", "r") as file:
    settingText = file.read()
settings = Setting.from_dict(json.loads(settingText))

client = BybitClient(
        is_testnet=settings.isTestnet,
        key=settings.key,
        secret_key=settings.secretKey
)

client.get_open_orders(
    symbol="USDCUSDT"
)