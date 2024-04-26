import json

from domain_models import CoinType
from schemas.setting import Setting
from services.bot import Side, OrderbookBridge, OrderManager

# Получаем настройки бота
with open("settings.json", "r") as file:
    settingText = file.read()
settings = Setting(**json.loads(settingText))
if settings.side == 0:
    side = Side.Buy
else:
    side = Side.Sell


# Получить все значения перечисления
coins_names = [member.value for name, member in CoinType.__members__.items()]
symbol = "USDCUSDT"
matches = []
for coin_name in coins_names:
    if coin_name in symbol:
        matches.append(coin_name)

if len(matches) != 2:
    raise ValueError()

print(symbol.index(matches[0]))

if symbol.index(matches[0]) == 0:
    right_pair = matches[1]
else:
    right_pair = matches[0]

print(right_pair)