from abc import ABC, abstractmethod
from datetime import datetime
from decimal import Decimal
from threading import Timer
from typing import Optional, Callable

from exceptions import WithoutTradeRangeException
from schemas import Ticker
from schemas.orderbook import Orderbook
from services.bot import Side, TradeRange
from services.bot.socket_bridges import TickerBridge, OrderbookBridge
from core.log import logger


class TradeTriggerBase(ABC):
    on_triggered: Optional[Callable[[Side], None]]

    def __init__(self):
        self.on_triggered = None

    @abstractmethod
    def set_range_and_restart(self, target_range: TradeRange):
        pass

    @abstractmethod
    def reset(self):
        pass


class TimeRangeTrigger(TradeTriggerBase):
    __top_range: TradeRange
    __bottom_range: TradeRange
    __timer: Optional[Timer]
    __values: list[Decimal]
    __trigger_duration_buy: int
    __side: Side

    def __init__(
            self,
            target_range: TradeRange,
            trigger_duration_buy: int,
            trigger_duration_sell: int,
            ticker_bridge: TickerBridge
    ):
        super().__init__()
        self.on_triggered = None
        self.__timer = None
        self.__values = list()
        self.__trigger_duration_buy = trigger_duration_buy
        self.__trigger_duration_sell = trigger_duration_sell
        self.__side = Side.Buy
        self.set_range_and_restart(target_range)
        ticker_bridge.message_event.subscribe(self.__push)

    def set_range_and_restart(self, target_range: TradeRange):
        accept_height = target_range.height
        r_top_top = target_range.sell + accept_height
        r_top_bottom = r_top_top - accept_height
        self.__top_range = TradeRange(r_top_bottom, r_top_top)
        r_bottom_top = target_range.buy
        r_bottom_bottom = r_bottom_top - accept_height
        self.__bottom_range = TradeRange(r_bottom_bottom, r_bottom_top)
        logger.info(f"{datetime.now()} SET TRIGGER AREA "
                    f"BUY [{r_top_top},{r_top_bottom}] "
                    f"SELL [{r_bottom_bottom} out:{r_bottom_top}]")
        self.reset()

    def __push(self, ticker: Ticker):
        is_trigger_start = self.__timer is not None
        if is_trigger_start:
            self.__values.append(ticker.last_price)

        if not is_trigger_start:
            is_trigger_area = ticker.last_price >= self.__top_range.sell or ticker.last_price <= self.__bottom_range.buy

            if is_trigger_area:
                self.__values = list()

                if ticker.last_price >= self.__top_range.buy:
                    self.__side = Side.Sell
                    trigger_duration = self.__trigger_duration_sell
                else:
                    self.__side = Side.Buy
                    trigger_duration = self.__trigger_duration_buy

                self.__values.append(ticker.last_price)
                self.__timer = Timer(trigger_duration, self.__trigger)
                self.__timer.start()
                logger.info(f"TRIGGER TIME START\n"
                            f"side:{self.__side.value} price:{ticker.last_price}")

        is_outside_top_trigger_area = self.__side == Side.Sell and ticker.last_price < self.__top_range.buy
        is_outside_bottom_trigger_area = self.__side == Side.Buy and ticker.last_price > self.__bottom_range.sell
        if is_trigger_start and (is_outside_top_trigger_area or is_outside_bottom_trigger_area):
            logger.info(f"TRIGGER TIME STOP "
                        f"side:{self.__side.value} price:{ticker.last_price}")
            self.reset()

    def __trigger(self):
        average_price = sum(self.__values) / len(self.__values)
        logger.info("TRIGGER TIME VALIDATE "
                    f"average_price:{average_price}")

        if self.__side == Side.Sell:
            offset_top = self.__top_range.sell - average_price
            offset_bottom = average_price - self.__top_range.buy

            if offset_top < offset_bottom or average_price >= self.__top_range.sell:
                if self.on_triggered:
                    self.on_triggered(self.__side)
                    logger.info("TRIGGER TIME SUCCESS "
                                f"average_price:{average_price}")
                    self.reset()
            else:
                self.reset()
        else:
            offset_top = self.__bottom_range.sell - average_price
            offset_bottom = average_price - self.__bottom_range.buy

            if offset_bottom < offset_top or average_price < self.__bottom_range.buy:
                if self.on_triggered:
                    self.on_triggered(self.__side)
                    self.reset()
            else:
                self.reset()

    def reset(self):
        logger.info(f"{self.__class__.__name__} RESET")
        if self.__timer:
            self.__timer.cancel()
        self.__timer = None
        self.__values = list()


class OrderbookTrigger(TradeTriggerBase):
    __is_triggered: bool
    __trade_range: TradeRange
    __min_bid_size: Decimal
    __min_ask_size: Decimal

    def __init__(
            self,
            orderbook_bridge: OrderbookBridge,
            trade_range: TradeRange,
            min_bid_size: Decimal,
            min_ask_size: Decimal,
            on_triggered: Callable[[Side], None] = None
    ):
        super().__init__()
        self.on_triggered = on_triggered
        self.__is_triggered = False
        self.__min_bid_size = min_bid_size
        self.__min_ask_size = min_ask_size
        self.set_range_and_restart(trade_range)
        self.__trade_range = trade_range

        orderbook_bridge.message_event.subscribe(self.__orderbook_handler)

    def set_range_and_restart(self, trade_range: TradeRange):
        logger.info(
            f"Установлен trade_range: {str(trade_range)} size[{self.__min_bid_size}, {self.__min_ask_size}]")
        self.__trade_range = trade_range
        self.reset()

    def reset(self):
        self.__is_triggered = False

    def __orderbook_handler(self, orderbook: Orderbook):
        if self.__is_triggered:
            return

        if not self.__validate_trade_range(orderbook):
            return

        nearest_bid = orderbook.bids[0]
        nearest_ask = orderbook.asks[0]

        self.__check_and_trigger(nearest_bid.size, self.__min_bid_size, Side.Buy)
        self.__check_and_trigger(nearest_ask.size, self.__min_ask_size, Side.Sell)

    def __check_and_trigger(self, size, min_size, side):
        if size <= min_size:
            self.__is_triggered = True
            if self.on_triggered:
                logger.info(f"Сработал триггер side:{side} min_size:{min_size} size:{size}")
                self.on_triggered(side)

    def __validate_trade_range(self, orderbook: Orderbook) -> bool:
        return orderbook.asks[0].price == self.__trade_range.sell
