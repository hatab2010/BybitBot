from typing import Any
from dataclasses import dataclass
from decimal import Decimal
from typing import List


#TODO переехать на Pydantic


# @dataclass
# class WebsocketResponse:
#     id: str
#     topic: str
#     creationTime: float
#     data: List[Order]
#
#     @staticmethod
#     def from_dict(obj: Any) -> 'WebsocketResponse':
#         _id = str(obj.get("id"))
#         _topic = str(obj.get("topic"))
#         _creationTime = float(obj.get("creationTime"))
#         _data = [Order.parse_obj(y) for y in obj.get("data")]
#         return WebsocketResponse(_id, _topic, _creationTime, _data)
#
#
# @dataclass
# class RestResponse:
#     retCode: int
#     retMsg: str
#     result: Any
#
#     @staticmethod
#     def from_dict(obj: Any) -> 'RestResponse':
#         _retCode = int(obj.get("retCode"))
#         _retMsg = str(obj.get("retMsg"))
#         _result = obj.get("result")
#         return RestResponse(_retCode, _retMsg, _result)


@dataclass
class LotSizeFilter:
    basePrecision: str
    quotePrecision: str
    minOrderQty: str
    maxOrderQty: str
    minOrderAmt: str
    maxOrderAmt: str

    @staticmethod
    def from_dict(obj: Any) -> 'LotSizeFilter':
        _basePrecision = str(obj.get("basePrecision"))
        _quotePrecision = str(obj.get("quotePrecision"))
        _minOrderQty = str(obj.get("minOrderQty"))
        _maxOrderQty = str(obj.get("maxOrderQty"))
        _minOrderAmt = str(obj.get("minOrderAmt"))
        _maxOrderAmt = str(obj.get("maxOrderAmt"))
        return LotSizeFilter(_basePrecision, _quotePrecision, _minOrderQty, _maxOrderQty, _minOrderAmt, _maxOrderAmt)


@dataclass
class PriceFilter:
    tick_size: Decimal

    @staticmethod
    def from_dict(obj: Any) -> 'PriceFilter':
        _tickSize = Decimal(obj.get("tickSize"))
        return PriceFilter(_tickSize)


@dataclass
class RiskParameters:
    limitParameter: str
    marketParameter: str

    @staticmethod
    def from_dict(obj: Any) -> 'RiskParameters':
        _limitParameter = str(obj.get("limitParameter"))
        _marketParameter = str(obj.get("marketParameter"))
        return RiskParameters(_limitParameter, _marketParameter)


@dataclass
class ListDatum:
    symbol: str
    baseCoin: str
    quoteCoin: str
    innovation: str
    status: str
    marginTrading: str
    lotSizeFilter: LotSizeFilter
    priceFilter: PriceFilter
    riskParameters: RiskParameters

    @staticmethod
    def from_dict(obj: Any) -> 'ListDatum':
        _symbol = str(obj.get("symbol"))
        _baseCoin = str(obj.get("baseCoin"))
        _quoteCoin = str(obj.get("quoteCoin"))
        _innovation = str(obj.get("innovation"))
        _status = str(obj.get("status"))
        _marginTrading = str(obj.get("marginTrading"))
        _lotSizeFilter = LotSizeFilter.from_dict(obj.get("lotSizeFilter"))
        _priceFilter = PriceFilter.from_dict(obj.get("priceFilter"))
        _riskParameters = RiskParameters.from_dict(obj.get("riskParameters"))
        return ListDatum(_symbol, _baseCoin, _quoteCoin, _innovation, _status, _marginTrading, _lotSizeFilter,
                         _priceFilter, _riskParameters)


@dataclass
class InstrumentInfo:
    category: str
    list: List[ListDatum]

    @staticmethod
    def from_dict(obj: Any) -> 'InstrumentInfo':
        _category = str(obj.get("category"))
        _list = [ListDatum.from_dict(y) for y in obj.get("list")]
        return InstrumentInfo(_category, _list)


# @dataclass
# class TickerData:
#     symbol: str
#     lastPrice: Decimal
#     highPrice24h: str
#     lowPrice24h: str
#     prevPrice24h: str
#     volume24h: str
#     turnover24h: str
#     price24hPcnt: str
#     usdIndexPrice: str
#
#     @staticmethod
#     def from_dict(obj: Any) -> 'TickerData':
#         _symbol = str(obj.get("symbol"))
#         _lastPrice = Decimal(obj.get("lastPrice"))
#         _highPrice24h = str(obj.get("highPrice24h"))
#         _lowPrice24h = str(obj.get("lowPrice24h"))
#         _prevPrice24h = str(obj.get("prevPrice24h"))
#         _volume24h = str(obj.get("volume24h"))
#         _turnover24h = str(obj.get("turnover24h"))
#         _price24hPcnt = str(obj.get("price24hPcnt"))
#         _usdIndexPrice = str(obj.get("usdIndexPrice"))
#         return TickerData(_symbol, _lastPrice, _highPrice24h, _lowPrice24h, _prevPrice24h, _volume24h, _turnover24h,
#                           _price24hPcnt, _usdIndexPrice)
#
#
# @dataclass
# class TickerResponse:
#     topic: str
#     ts: float
#     type: str
#     cs: float
#     data: TickerData
#
#     @staticmethod
#     def from_dict(obj: Any) -> 'TickerResponse':
#         _topic = str(obj.get("topic"))
#         _ts = float(obj.get("ts"))
#         _type = str(obj.get("type"))
#         _cs = float(obj.get("cs"))
#         _data = TickerData.from_dict(obj.get("data"))
#         return TickerResponse(_topic, _ts, _type, _cs, _data)


@dataclass
class Bayer:
    price: Decimal
    quantity: Decimal
