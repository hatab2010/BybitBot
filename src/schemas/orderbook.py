from decimal import Decimal

from pydantic import BaseModel, Field
from typing import List


class PriceVolume(BaseModel):
    price: Decimal
    volume: Decimal

    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not isinstance(v, list) or len(v) != 2:
            raise ValueError("price volume pair must be a list of two elements")
        price, volume = v
        return cls(price=price, volume=volume)


class OrderBook(BaseModel):
    symbol: str = Field(..., alias='s')
    bids: List[PriceVolume] = Field(..., alias='b')
    asks: List[PriceVolume] = Field(..., alias='a')
    update_id: int = Field(..., alias='u')
    sequence: int = Field(..., alias='seq')