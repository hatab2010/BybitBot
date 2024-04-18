from typing import Callable

from domain_models import Side, TradeRange
from triggers import TradeTriggerBase


class TriggerNode:
    sell_signal_priority: int
    buy_signal_priority: int
    trigger: TradeTriggerBase

    def __init__(self, trigger):
        self.trigger = trigger


class TradeTriggerSwitcher:
    on_price_change: Callable[[Side], None]

    __triggers: [TradeTriggerBase]

    def __init__(self):
        pass

    def set_trigger_range(self, trade_range: TradeRange):
        for trigger in self.__triggers:
            trigger.set_range_and_restart(trade_range)


class TriggerMix(TradeTriggerBase):
    __buy_trigger: TradeTriggerBase
    __sell_trigger: TradeTriggerBase

    def set_range_and_restart(self, target_range: TradeRange):
        pass

    def __int__(
            self,
            buy_trigger: TradeTriggerBase,
            sell_trigger: TradeTriggerBase
    ):
        self.__buy_trigger = buy_trigger
        self.__sell_trigger = sell_trigger


    def on_sell_triggered(self):
        pass

    def on_buy_triggered(self):
        pass