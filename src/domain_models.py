from decimal import Decimal
from enum import Enum
from typing import Union


class OrderStatus(str, Enum):
    Filled = "Filled",
    New = "New",
    Cancelled = "Cancelled"

    def __str__(self):
        return self.value


class CoinType(str, Enum):
    USDT = "USDT",
    USDC = "USDC"

    def __str__(self):
        return self.value


# class Direction(str, Enum):
#     Up = "Up",
#     Down = "Down"


class Side(str, Enum):
    Buy = "Buy",
    Sell = "Sell"

    def __str__(self):
        return self.value


class TradeRange:
    __sell: Decimal
    __buy: Decimal

    def __init__(self, buy: Decimal, sell: Decimal):
        self.__buy = buy
        self.__sell = sell

    @property
    def sell(self) -> Decimal:
        return self.__sell

    @property
    def buy(self) -> Decimal:
        return self.__buy

    @property
    def height(self) -> Decimal:
        return abs(self.__sell - self.__buy)

    def offset(self, step_offset: Union[int, Decimal]):
        length = self.height * step_offset
        self.__sell = self.__sell + length
        self.__buy = self.__buy + length

    def __str__(self):
        return f"[{self.__buy}, {self.__sell}]"
