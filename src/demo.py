import json
import time
from decimal import Decimal

from pydantic import ValidationError, validate_call, model_validator, validator, field_validator
from pybit.unified_trading import WebSocket
from pydantic_core.core_schema import ValidationInfo

from schemas import EventMessage, Orderbook
from typing import List, Dict, Any
from pydantic import BaseModel, Field

from typing import List, Tuple

from typing import List
from pydantic import BaseModel, Field, ValidationError

from schemas.orderbook import PriceVolume


class Offer(BaseModel):
    price: Decimal
    size: Decimal

    @model_validator(mode='before')
    def validate(cls, data):
        if not "price" in data and not "size" in data and len(data) == 2:
            data = {'price': Decimal(data[0]), "size": Decimal(data[1])}
        return data


class DataModel(BaseModel):
    symbol: str = Field(alias='s')
    bids: List[Offer] = Field(alias='b')
    asks: List[Tuple[str, str]] = Field(alias='a')
    u: int
    sequence: int = Field(..., alias='seq')

volumes = {"price":Decimal("1.1"), "size":Decimal("1.1")}
offer = PriceVolume(**volumes)
print(f"offer {offer}")
# Пример исходных данных
json_data = {
    's': 'USDCUSDT',
    'b': [['0.9995', '263644.14']],
    'a': [['0.9996', '980438.64']],
    'u': 1182242,
    'seq': 36962400367
}

try:
    model = DataModel(**json_data)
except ValidationError as e:
    print("Validation Error:", e)
else:
    print(model)
    print("Bids:", model.bids)  # Список объектов Offer
    print("Asks:", model.asks)  # Список объектов Offer

#
#
# def callback(message):
#     response = EventMessage(**message)
#     print(response.data)
#
#     try:
#         orderbook = Orderbook(**response.data)
#     except ValidationError as ex:
#         print(ex)
#     except Exception as ex:
#         print(ex)
#         raise ex
#
#     print(orderbook)
#
#
# socket = WebSocket(
#     testnet=False,
#     channel_type="spot"
# )
#
# socket.orderbook_stream(1, "USDCUSDT", callback)
#
# while True:
#     time.sleep(1)
#
