from typing import Any
from dataclasses import dataclass
from decimal import Decimal
from typing import List

@dataclass
class Setting:
    isTestnet: bool
    key: str
    secretKey: str
    buyPrice: float
    sellPrice: float
    tradeAmount: int
    orderCount: int
    symbol: str

    @staticmethod
    def from_dict(obj: Any) -> 'Setting':
        _isTestnet = bool(obj.get("isTestnet"))
        _key = str(obj.get("key"))
        _secretKey = str(obj.get("secretKey"))
        _buyPrice = float(obj.get("buyPrice"))
        _sellPrice = float(obj.get("sellPrice"))
        _tradeAmount = int(obj.get("tradeAmount"))
        _orderCount = int(obj.get("orderCount"))
        _symbol = str(obj.get("symbol"))
        return Setting(_isTestnet, _key, _secretKey, _buyPrice, _sellPrice, _tradeAmount, _orderCount, _symbol)


import json
@dataclass
class Datum:
    symbol: str
    orderId: str
    side: str
    orderType: str
    cancelType: str
    price: str
    qty: str
    orderIv: str
    timeInForce: str
    orderStatus: str

    @staticmethod
    def from_dict(obj: Any) -> 'Datum':
        _symbol = str(obj.get("symbol"))
        _orderId = str(obj.get("orderId"))
        _side = str(obj.get("side"))
        _orderType = str(obj.get("orderType"))
        _cancelType = str(obj.get("cancelType"))
        _price = str(obj.get("price"))
        _qty = str(obj.get("qty"))
        _orderIv = str(obj.get("orderIv"))
        _timeInForce = str(obj.get("timeInForce"))
        _orderStatus = str(obj.get("orderStatus"))
        return Datum(_symbol, _orderId, _side, _orderType, _cancelType, _price, _qty, _orderIv, _timeInForce, _orderStatus)


@dataclass
class WebsocketResponse:
    id: str
    topic: str
    creationTime: float
    data: List[Datum]

    @staticmethod
    def from_dict(obj: Any) -> 'WebsocketResponse':
        _id = str(obj.get("id"))
        _topic = str(obj.get("topic"))
        _creationTime = float(obj.get("creationTime"))
        _data = [Datum.from_dict(y) for y in obj.get("data")]
        return WebsocketResponse(_id, _topic, _creationTime, _data)


@dataclass
class RestResponse:
    retCode: int
    retMsg: str
    result: str

    @staticmethod
    def from_dict(obj: Any) -> 'RestResponse':
        _retCode = int(obj.get("retCode"))
        _retMsg = str(obj.get("retMsg"))
        _result = str(obj.get("result"))
        return RestResponse(_retCode, _retMsg, _result)

