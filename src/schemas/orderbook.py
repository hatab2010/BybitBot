from decimal import Decimal
from typing import List

from pydantic import BaseModel, Field, model_validator


class PriceVolume(BaseModel):
    price: Decimal
    size: Decimal

    @model_validator(mode="before")
    def validate(cls, data):
        if not "price" in data and not "size" in data and len(data) == 2:
            data = {'price': Decimal(data[0]), "size": Decimal(data[1])}
        return data

    def __str__(self):
        return f"[{self.price}, {self.size}]"

    def __repr__(self):
        return f"[{self.price}, {self.size}]"


class Orderbook(BaseModel):
    symbol: str = Field(alias='s')
    bids: List[PriceVolume] = Field(alias='b')
    asks: List[PriceVolume] = Field(alias='a')
    update_id: int = Field(alias='u')
    sequence: int = Field(alias='seq')
