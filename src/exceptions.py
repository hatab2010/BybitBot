from abc import ABC
from domain_models import TradeRange


class DomainException(ABC, Exception):
    pass


class TriggerException(DomainException):
    pass


class WithoutTradeRangeException(TriggerException):
    def __init__(self, trade_range: TradeRange, current_range: TradeRange):
        super().__init__(f"Ошибка. Неверно указан торговый канал. "
                         f"trade_range: {trade_range.buy}-{trade_range.sell} "
                         f"market_range: {current_range.buy}-{current_range.sell}")
