from abc import ABC, abstractmethod
from datetime import datetime
from decimal import Decimal
from threading import Timer
from typing import Optional, Callable

from exceptions import WithoutTradeRangeException
from schemas import Ticker
from schemas.orderbook import PriceVolume, Orderbook
from services.bot import Side, TradeRange
from services.bot.socket_bridges import TickerEvent, TickerBridge, OrderbookBridge


class TradeTriggerBase(ABC):
    on_triggered: Optional[Callable[[Side], None]]

    def __init__(self):
        self.on_triggered = None

    @abstractmethod
    def set_range(self, target_range: TradeRange):
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
        self.triggered = None
        self.__timer = None
        self.__values = list()
        self.__trigger_duration_buy = trigger_duration_buy
        self.__trigger_duration_sell = trigger_duration_sell
        self.__side = Side.Buy
        self.set_range(target_range)
        ticker_bridge.message_event.subscribe(self.__push)

    def set_range(self, target_range: TradeRange):
        accept_height = target_range.height
        r_top_top = target_range.sell + accept_height
        r_top_bottom = r_top_top - accept_height
        self.__top_range = TradeRange(r_top_top, r_top_bottom)
        r_bottom_top = target_range.buy
        r_bottom_bottom = r_bottom_top - accept_height
        self.__bottom_range = TradeRange(r_bottom_top, r_bottom_bottom)
        print(f"{datetime.now()} SET TRIGGER AREA\n"
              f"BUY in:{r_top_top} out:{r_top_bottom}\n"
              f"SELL in:{r_bottom_bottom} out:{r_bottom_top}")
        self.reset()

    def __push(self, ticker: Ticker) -> None:
        is_trigger_start = self.__timer is not None
        if is_trigger_start:
            self.__values.append(ticker.last_price)

        if not is_trigger_start:
            is_trigger_area = ticker.last_price >= self.__top_range.sell or ticker.last_price <= self.__bottom_range.buy

            if is_trigger_area:
                self.__values = list()

                if ticker.last_price >= self.__top_range.buy:
                    self.__side = Side.Buy
                    trigger_duration = self.__trigger_duration_buy
                else:
                    self.__side = Side.Sell
                    trigger_duration = self.__trigger_duration_sell

                self.__values.append(ticker.last_price)
                self.__timer = Timer(trigger_duration, self.__trigger)
                self.__timer.start()
                print(f"{datetime.now()} TRIGGER START\n"
                      f"side:{self.__side.value} price:{ticker.last_price}")

        is_outside_top_trigger_area = self.__side == Side.Buy and ticker.last_price < self.__top_range.buy
        is_outside_bottom_trigger_area = self.__side == Side.Sell and ticker.last_price > self.__bottom_range.sell
        if is_trigger_start and (is_outside_top_trigger_area or is_outside_bottom_trigger_area):
            print(f"{datetime.now()} TRIGGER STOP\n"
                  f"side:{self.__side.value} price:{ticker.last_price}")
            self.reset()

    def __trigger(self):
        average_price = sum(self.__values) / len(self.__values)
        print("TRIGGER\n"
              f"average_price:{average_price}")

        if self.__side == Side.Buy:
            offset_top = self.__top_range.sell - average_price
            offset_bottom = average_price - self.__top_range.buy

            if offset_top < offset_bottom or average_price >= self.__top_range.sell:
                if self.triggered:
                    self.triggered(self.__side)
                    self.reset()
            else:
                self.reset()
        else:
            offset_top = self.__bottom_range.sell - average_price
            offset_bottom = average_price - self.__bottom_range.buy

            if offset_bottom < offset_top or average_price < self.__bottom_range.buy:
                if self.triggered:
                    self.triggered(self.__side)
                    self.reset()
            else:
                self.reset()

    def reset(self):
        print(f"{self.__class__.__name__} RESET")
        if self.__timer:
            self.__timer.cancel()
        self.__timer = None
        self.__values = list()


class OrderbookTrigger(TradeTriggerBase):
    __is_finalized: bool
    __trade_range: TradeRange
    __min_bid_size: Decimal
    __min_ask_size: Decimal

    def __init__(
            self,
            orderbook_bridge: OrderbookBridge,
            trade_range: TradeRange,
            min_bid_size: Decimal,
            min_ask_size: Decimal
    ):
        self.__is_finalized = False
        self.__trade_range = trade_range
        self.__min_bid_size = min_bid_size
        self.__min_ask_size = min_ask_size

        orderbook_bridge.message_event.subscribe(self.orderbook_handler)

    def set_range(self, trade_range: TradeRange):
        raise NotImplemented()

    def orderbook_handler(self, orderbook: Orderbook):
        if self.__is_finalized:
            return

        self.__validate_trade_range(orderbook)

        nearest_bid = orderbook.bids[0]
        nearest_ask = orderbook.asks[0]

        if nearest_bid.size <= self.__min_bid_size:

    def reset(self):
        self.__is_finalized = False

    def __validate_trade_range(self, orderbook: Orderbook):
        if orderbook.asks[0].price != self.__trade_range.buy:
            raise WithoutTradeRangeException(
                self.__trade_range,
                TradeRange(orderbook.bids[0].price, orderbook.asks[0].price)
            )
