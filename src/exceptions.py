from decimal import Decimal
from typing import Union

from domain_models import TradeRange


class WithoutTradeRangeException(Exception):
    def __init__(self, trade_range: TradeRange, current_range: TradeRange):
        super().__init__(f"trade_range: {vars(trade_range)}\n"
                         f"market_range: {vars(current_range)}")
